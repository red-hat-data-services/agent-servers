from __future__ import annotations

import json
import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import Settings

logger = logging.getLogger(__name__)

MAX_SCAN_DEPTH = 6


@dataclass
class CodexSkill:
    name: str
    description: str
    short_description: str | None = None
    display_name: str | None = None
    default_prompt: str | None = None
    scope: str = "user"
    source_path: str = ""
    plugin_name: str | None = None


@dataclass
class CodexConfig:
    model: str | None = None
    provider: str | None = None
    sandbox_mode: str | None = None
    mcp_server_count: int = 0


@dataclass
class ScanResult:
    skills: list[CodexSkill] = field(default_factory=list)
    config: CodexConfig = field(default_factory=CodexConfig)
    plugin_count: int = 0


class SkillScanner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def scan(self) -> ScanResult:
        skills = self._scan_skills()
        skills = self._deduplicate(skills)
        config = self._parse_config()
        plugin_count = 0
        if self._settings.scan_plugins:
            plugin_skills, plugin_count = self._scan_plugins()
            existing_names = {s.name for s in skills}
            for ps in plugin_skills:
                if ps.name not in existing_names:
                    skills.append(ps)
                    existing_names.add(ps.name)

        return ScanResult(
            skills=skills,
            config=config,
            plugin_count=plugin_count,
        )

    def _scan_skills(self) -> list[CodexSkill]:
        base = self._settings.resolved_base_dir
        project = self._settings.resolved_project_dir
        skills: list[CodexSkill] = []

        scan_roots: list[tuple[Path, str]] = []

        if project:
            scan_roots.append((project / ".codex" / "skills", "repo"))
            scan_roots.append((project / ".agents" / "skills", "repo"))

        skills_dir = base / "skills"
        scan_roots.append((skills_dir, "user"))

        if self._settings.scan_system_skills:
            scan_roots.append((skills_dir / ".system", "system"))

        if self._settings.scan_admin_skills:
            scan_roots.append((Path("/etc/codex/skills"), "admin"))

        for root, scope in scan_roots:
            skills.extend(self._scan_directory(root, scope))

        return skills

    def _scan_directory(self, root: Path, scope: str) -> list[CodexSkill]:
        if not root.is_dir():
            return []

        skills: list[CodexSkill] = []
        try:
            for entry in sorted(root.iterdir()):
                if not entry.is_dir():
                    continue
                if entry.name.startswith(".") and scope != "system":
                    continue

                skill_md = entry / "SKILL.md"
                if not skill_md.is_file():
                    self._scan_nested(entry, scope, skills, depth=1)
                    continue

                skill = self._parse_skill(skill_md, scope)
                if skill:
                    skills.append(skill)
        except PermissionError:
            logger.warning("Permission denied scanning %s", root)

        return skills

    def _scan_nested(
        self, directory: Path, scope: str, skills: list[CodexSkill], depth: int
    ) -> None:
        if depth >= MAX_SCAN_DEPTH:
            return
        if not directory.is_dir():
            return

        try:
            for entry in sorted(directory.iterdir()):
                if not entry.is_dir():
                    continue
                if entry.name.startswith(".") and scope != "system":
                    continue

                skill_md = entry / "SKILL.md"
                if skill_md.is_file():
                    skill = self._parse_skill(skill_md, scope)
                    if skill:
                        skills.append(skill)
                else:
                    self._scan_nested(entry, scope, skills, depth + 1)
        except PermissionError:
            logger.warning("Permission denied scanning %s", directory)

    def _parse_skill(self, skill_md: Path, scope: str) -> CodexSkill | None:
        try:
            text = skill_md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            logger.warning("Failed to read %s", skill_md)
            return None

        frontmatter = _parse_frontmatter(text)
        if not frontmatter:
            logger.warning("No valid frontmatter in %s", skill_md)
            return None

        description = (frontmatter.get("description") or "").strip()
        if not description:
            logger.warning("Missing description in %s", skill_md)
            return None

        name = frontmatter.get("name") or skill_md.parent.name
        metadata = frontmatter.get("metadata", {}) or {}

        display_name = None
        short_description = metadata.get("short-description")
        default_prompt = None

        openai_yaml = skill_md.parent / "agents" / "openai.yaml"
        if openai_yaml.is_file():
            ui = self._parse_openai_yaml(openai_yaml)
            display_name = ui.get("display_name") or display_name
            short_description = ui.get("short_description") or short_description
            default_prompt = ui.get("default_prompt") or default_prompt

        return CodexSkill(
            name=name,
            description=description,
            short_description=short_description,
            display_name=display_name,
            default_prompt=default_prompt,
            scope=scope,
            source_path=str(skill_md.parent),
        )

    def _parse_openai_yaml(self, path: Path) -> dict:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to parse %s", path)
            return {}

        if not isinstance(data, dict):
            return {}

        interface = data.get("interface", {}) or {}
        result = {}
        if interface.get("display_name"):
            result["display_name"] = interface["display_name"]
        if interface.get("short_description"):
            result["short_description"] = interface["short_description"]

        prompt = interface.get("default_prompt")
        if isinstance(prompt, list):
            result["default_prompt"] = " ".join(str(p) for p in prompt)
        elif isinstance(prompt, str):
            result["default_prompt"] = prompt

        return result

    def _scan_plugins(self) -> tuple[list[CodexSkill], int]:
        plugins_dir = self._settings.resolved_base_dir / "plugins"
        if not plugins_dir.is_dir():
            return [], 0

        skills: list[CodexSkill] = []
        plugin_count = 0

        try:
            for entry in sorted(plugins_dir.iterdir()):
                if not entry.is_dir():
                    continue

                manifest = entry / ".codex-plugin" / "plugin.json"
                if not manifest.is_file():
                    continue

                plugin_count += 1
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    logger.warning("Failed to parse plugin manifest %s", manifest)
                    continue

                plugin_name = data.get("name", entry.name)
                skills_path = data.get("skills")
                if not skills_path:
                    continue

                plugin_skills_dir = entry / skills_path
                if not plugin_skills_dir.is_dir():
                    continue

                for skill_dir in sorted(plugin_skills_dir.iterdir()):
                    if not skill_dir.is_dir():
                        continue
                    skill_md = skill_dir / "SKILL.md"
                    if not skill_md.is_file():
                        continue
                    skill = self._parse_skill(skill_md, "plugin")
                    if skill:
                        skill.plugin_name = plugin_name
                        skills.append(skill)
        except PermissionError:
            logger.warning("Permission denied scanning %s", plugins_dir)

        return skills, plugin_count

    def _parse_config(self) -> CodexConfig:
        paths = [self._settings.resolved_base_dir / "config.toml"]
        project = self._settings.resolved_project_dir
        if project:
            paths.append(project / ".codex" / "config.toml")

        merged: dict = {}
        for path in paths:
            if not path.is_file():
                continue
            try:
                with open(path, "rb") as f:
                    data = tomllib.load(f)
                merged.update(data)
            except Exception:
                logger.warning("Failed to parse %s", path)

        return CodexConfig(
            model=merged.get("model"),
            provider=merged.get("model_provider"),
            sandbox_mode=merged.get("sandbox_mode"),
            mcp_server_count=len(merged.get("mcp_servers", {})),
        )

    def _deduplicate(self, skills: list[CodexSkill]) -> list[CodexSkill]:
        seen: dict[str, CodexSkill] = {}
        scope_priority = {"repo": 0, "user": 1, "system": 2, "admin": 3, "plugin": 4}
        for skill in skills:
            existing = seen.get(skill.name)
            if existing is None:
                seen[skill.name] = skill
            else:
                existing_priority = scope_priority.get(existing.scope, 99)
                new_priority = scope_priority.get(skill.scope, 99)
                if new_priority < existing_priority:
                    seen[skill.name] = skill
        return list(seen.values())


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}
    try:
        result = yaml.safe_load(text[3:end])
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}
