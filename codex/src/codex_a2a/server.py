import time
from typing import Any

from fastapi import FastAPI

from .agent_card import A2ACard, build_agent_card
from .config import Settings
from .skill_scanner import SkillScanner


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title=settings.a2a_title, version=settings.a2a_version)
    scanner = SkillScanner(settings)
    _cache: dict[str, Any] = {"card": None, "expires": 0.0}

    @app.get("/.well-known/agent-card.json", response_model=A2ACard, response_model_exclude_none=True)
    @app.get("/.well-known/agent.json", response_model=A2ACard, response_model_exclude_none=True)
    async def agent_card() -> A2ACard:
        now = time.monotonic()
        if _cache["card"] and now < _cache["expires"]:
            return _cache["card"]

        card = await build_agent_card(settings, scanner)
        _cache["card"] = card
        _cache["expires"] = now + settings.cache_ttl_seconds
        return card

    @app.get("/health")
    async def health() -> dict:
        return {"healthy": True}

    return app
