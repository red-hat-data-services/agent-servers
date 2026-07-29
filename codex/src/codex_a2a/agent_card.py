from __future__ import annotations

import asyncio

from pydantic import BaseModel

from .config import Settings
from .skill_scanner import CodexSkill, ScanResult, SkillScanner


class A2ASkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
    examples: list[str] | None = None


class A2AProvider(BaseModel):
    organization: str | None = None
    url: str | None = None


class A2AInterface(BaseModel):
    url: str
    protocolBinding: str = "HTTP+JSON"
    protocolVersion: str


class A2ACapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False


class A2ACard(BaseModel):
    name: str
    description: str
    version: str
    supportedInterfaces: list[A2AInterface]
    capabilities: A2ACapabilities
    defaultInputModes: list[str]
    defaultOutputModes: list[str]
    skills: list[A2ASkill]
    provider: A2AProvider | None = None
    documentationUrl: str | None = None
    iconUrl: str | None = None


FALLBACK_SKILL = A2ASkill(
    id="codex.chat",
    name="Codex Chat",
    description="AI coding agent for code generation, editing, review, and debugging",
    tags=["codex", "coding", "agent"],
    examples=[
        "Fix the failing test in auth.py",
        "Refactor this module to use async/await",
        "Explain what this function does",
    ],
)


def _map_skill(skill: CodexSkill) -> A2ASkill:
    tags = ["codex", skill.scope]
    if skill.plugin_name:
        tags.append(skill.plugin_name)

    return A2ASkill(
        id=f"codex.{skill.name}",
        name=skill.display_name or skill.name.replace("-", " ").title(),
        description=skill.short_description or skill.description,
        tags=tags,
        examples=[skill.default_prompt] if skill.default_prompt else None,
    )


def _build_skills(scan: ScanResult) -> list[A2ASkill]:
    if not scan.skills:
        return [FALLBACK_SKILL]
    return [_map_skill(s) for s in scan.skills]


def _build_description(base: str, scan: ScanResult) -> str:
    parts = [f"{base.rstrip('.')}."]
    if scan.skills:
        count = len(scan.skills)
        parts.append(f"{count} skill{'s' if count != 1 else ''} discovered.")
    if scan.config.model:
        parts.append(f"Model: {scan.config.model}.")
    if scan.config.mcp_server_count:
        n = scan.config.mcp_server_count
        parts.append(f"{n} MCP server{'s' if n != 1 else ''} configured.")
    if scan.plugin_count:
        n = scan.plugin_count
        parts.append(f"{n} plugin{'s' if n != 1 else ''} installed.")
    return " ".join(parts)


async def build_agent_card(settings: Settings, scanner: SkillScanner) -> A2ACard:
    scan = await asyncio.to_thread(scanner.scan)

    provider = None
    if settings.a2a_provider_org or settings.a2a_provider_url:
        provider = A2AProvider(
            organization=settings.a2a_provider_org,
            url=settings.a2a_provider_url,
        )

    return A2ACard(
        name=settings.a2a_title,
        description=_build_description(settings.a2a_description, scan),
        version=settings.a2a_version,
        supportedInterfaces=[
            A2AInterface(
                url=settings.public_url,
                protocolVersion=settings.a2a_version,
            ),
        ],
        capabilities=A2ACapabilities(),
        defaultInputModes=settings.input_modes_list,
        defaultOutputModes=settings.output_modes_list,
        skills=_build_skills(scan),
        provider=provider,
        documentationUrl=settings.a2a_documentation_url,
        iconUrl=settings.a2a_icon_url,
    )
