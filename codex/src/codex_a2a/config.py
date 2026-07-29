from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    base_dir: str = Field(
        default="~/.codex",
        alias="CODEX_A2A_BASE_DIR",
    )
    project_dir: str | None = Field(
        default=None,
        alias="CODEX_A2A_PROJECT_DIR",
    )
    scan_system_skills: bool = Field(
        default=False,
        alias="CODEX_SCAN_SYSTEM",
    )
    scan_admin_skills: bool = Field(
        default=False,
        alias="CODEX_SCAN_ADMIN",
    )
    scan_plugins: bool = Field(
        default=True,
        alias="CODEX_SCAN_PLUGINS",
    )

    a2a_host: str = Field(default="127.0.0.1", alias="A2A_HOST")
    a2a_port: int = Field(default=8200, alias="A2A_PORT")
    a2a_public_url: str | None = Field(default=None, alias="A2A_PUBLIC_URL")

    a2a_title: str = Field(default="Codex", alias="A2A_TITLE")
    a2a_description: str = Field(
        default="AI-powered coding agent by OpenAI",
        alias="A2A_DESCRIPTION",
    )
    a2a_version: str = Field(default="1.0.1", alias="A2A_VERSION")

    a2a_documentation_url: str | None = Field(
        default="https://codex.openai.com/docs",
        alias="A2A_DOCUMENTATION_URL",
    )
    a2a_provider_org: str | None = Field(
        default="OpenAI",
        alias="A2A_PROVIDER_ORG",
    )
    a2a_provider_url: str | None = Field(
        default="https://openai.com",
        alias="A2A_PROVIDER_URL",
    )
    a2a_icon_url: str | None = Field(default=None, alias="A2A_ICON_URL")

    a2a_input_modes: str = Field(
        default="text/plain",
        alias="A2A_INPUT_MODES",
    )
    a2a_output_modes: str = Field(
        default="text/plain,application/json",
        alias="A2A_OUTPUT_MODES",
    )

    cache_ttl_seconds: int = Field(default=30, alias="CACHE_TTL_SECONDS")

    @property
    def public_url(self) -> str:
        if self.a2a_public_url:
            return self.a2a_public_url
        return f"http://{self.a2a_host}:{self.a2a_port}"

    @property
    def resolved_base_dir(self) -> Path:
        return Path(self.base_dir).expanduser().resolve()

    @property
    def resolved_project_dir(self) -> Path | None:
        if self.project_dir:
            return Path(self.project_dir).expanduser().resolve()
        return None

    @property
    def input_modes_list(self) -> list[str]:
        return [m.strip() for m in self.a2a_input_modes.split(",") if m.strip()]

    @property
    def output_modes_list(self) -> list[str]:
        return [m.strip() for m in self.a2a_output_modes.split(",") if m.strip()]
