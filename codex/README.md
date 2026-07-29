# Codex A2A Agent Card Server

A lightweight server that serves an [A2A (Agent-to-Agent)](https://a2a-protocol.org/) agent card for [Codex CLI](https://github.com/openai/codex). It discovers Codex skills, plugins, and configuration by scanning the filesystem — no connection to a running Codex process required.

## Prerequisites

- Python 3.11+
- Codex CLI installed (for skills/config to discover)

## Quick Start

```bash
pip install -e .
codex-a2a
```

The server starts on `http://127.0.0.1:8200` by default.

## Endpoints

| Path | Description |
|---|---|
| `/.well-known/agent-card.json` | A2A v1.0.1 agent card |
| `/.well-known/agent.json` | Same card (legacy path) |
| `/health` | Health check |
| `/docs` | Swagger UI |

## Configuration

All settings can be configured via environment variables or a `.env` file. See [.env.example](.env.example) for the full list.

### Filesystem Scan

The server scans a base directory for Codex assets:

```
$CODEX_A2A_BASE_DIR/           # default: ~/.codex
  skills/                      # user-scoped skills (dirs containing SKILL.md)
  skills/.system/              # bundled skills (opt-in via CODEX_SCAN_SYSTEM=true)
  plugins/                     # plugins with .codex-plugin/plugin.json
  config.toml                  # Codex configuration (model, MCP servers)
```

Optionally, set `CODEX_A2A_PROJECT_DIR` for repo-scoped skills:

```
$CODEX_A2A_PROJECT_DIR/
  .codex/skills/               # repo-scoped skills
  .agents/skills/              # repo-scoped skills (alternate convention)
  .codex/config.toml           # project-level config overrides
```

### Container Deployment

Mount your Codex data directory and set the base dir:

```bash
docker run -v /host/codex-data:/data/codex \
  -e CODEX_A2A_BASE_DIR=/data/codex \
  -p 8200:8200 \
  codex-a2a
```

### Key Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CODEX_A2A_BASE_DIR` | `~/.codex` | Root directory to scan |
| `CODEX_A2A_PROJECT_DIR` | (none) | Project dir for repo-scoped skills |
| `A2A_HOST` | `127.0.0.1` | Server bind host |
| `A2A_PORT` | `8200` | Server bind port |
| `A2A_TITLE` | `Codex` | Agent name in the card |
| `A2A_DESCRIPTION` | `AI-powered coding agent by OpenAI` | Agent description |
| `A2A_INPUT_MODES` | `text/plain` | Comma-separated input MIME types |
| `A2A_OUTPUT_MODES` | `text/plain,application/json` | Comma-separated output MIME types |

## CLI Options

```
codex-a2a [--port PORT] [--base-dir DIR] [--project-dir DIR]
          [--env-file FILE] [--include-system]
```

CLI flags override environment variables.
