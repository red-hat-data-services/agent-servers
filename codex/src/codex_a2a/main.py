import argparse
import sys

import uvicorn

from .config import Settings
from .server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codex-a2a",
        description="A2A agent card server for Codex CLI",
    )
    parser.add_argument("--port", type=int, default=None, help="Server port")
    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="Base directory containing Codex skills/plugins/config (default: ~/.codex)",
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory for repo-scoped skills",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include system/bundled skills in the agent card",
    )
    args = parser.parse_args()

    try:
        settings = Settings(_env_file=args.env_file)
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        sys.exit(1)

    if args.port is not None:
        settings.a2a_port = args.port
    if args.base_dir is not None:
        settings.base_dir = args.base_dir
    if args.project_dir is not None:
        settings.project_dir = args.project_dir
    if args.include_system:
        settings.scan_system_skills = True

    app = create_app(settings)

    print("Codex A2A Server")
    print(f"  Server:     http://{settings.a2a_host}:{settings.a2a_port}")
    print(f"  Base dir:   {settings.resolved_base_dir}")
    if settings.resolved_project_dir:
        print(f"  Project:    {settings.resolved_project_dir}")
    print(
        f"  Agent card: http://{settings.a2a_host}:{settings.a2a_port}/.well-known/agent-card.json"
    )
    print(f"  Swagger:    http://{settings.a2a_host}:{settings.a2a_port}/docs")
    print()

    uvicorn.run(app, host=settings.a2a_host, port=settings.a2a_port)


if __name__ == "__main__":
    main()
