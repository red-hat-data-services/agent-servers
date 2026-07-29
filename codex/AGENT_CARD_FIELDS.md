# Agent Card Field Reference

How each A2A v1.0.1 agent card field is populated.

## Required Fields

| Field | Source | Type |
|---|---|---|
| `name` | `A2A_TITLE` env var | Configurable, default `"Codex"` |
| `description` | `A2A_DESCRIPTION` env var + dynamic enrichment (skill count, model, MCP server count, plugin count) | Configurable base + dynamic |
| `version` | `A2A_VERSION` env var | Configurable, default `"1.0.1"` |
| `supportedInterfaces` | Computed from `A2A_PUBLIC_URL` or `A2A_HOST`/`A2A_PORT` | Dynamic |
| `supportedInterfaces[].url` | Computed from server settings | Dynamic |
| `supportedInterfaces[].protocolBinding` | Hardcoded `"HTTP+JSON"` | Static |
| `supportedInterfaces[].protocolVersion` | `A2A_VERSION` env var | Configurable |
| `capabilities.streaming` | Hardcoded `false` | Static — will be enabled when full A2A task execution is implemented via the stdio bridge to codex app-server |
| `capabilities.pushNotifications` | Hardcoded `false` | Static — will be enabled when full A2A task execution is implemented via the stdio bridge to codex app-server |
| `defaultInputModes` | `A2A_INPUT_MODES` env var (comma-separated) | Configurable, default `["text/plain"]` |
| `defaultOutputModes` | `A2A_OUTPUT_MODES` env var (comma-separated) | Configurable, default `["text/plain", "application/json"]` |
| `skills` | Scanned from filesystem `SKILL.md` files | Dynamic |

## Skill Fields

| Field | Source |
|---|---|
| `skills[].id` | `"codex."` + skill `name` from frontmatter (or directory name) |
| `skills[].name` | `display_name` from `agents/openai.yaml`, or titlecased skill name |
| `skills[].description` | `short_description` from metadata/openai.yaml, or `description` from frontmatter |
| `skills[].tags` | `["codex", scope]` + plugin name if applicable |
| `skills[].examples` | `default_prompt` from `agents/openai.yaml` (if present) |

When no skills are found on disk, a single fallback `codex.chat` skill is used.

## Optional Fields

| Field | Source | Included When |
|---|---|---|
| `provider.organization` | `A2A_PROVIDER_ORG` env var | Set (default: `"OpenAI"`) |
| `provider.url` | `A2A_PROVIDER_URL` env var | Set (default: `"https://openai.com"`) |
| `documentationUrl` | `A2A_DOCUMENTATION_URL` env var | Set (default: `"https://codex.openai.com/docs"`) |
| `iconUrl` | `A2A_ICON_URL` env var | Set (default: none) |

## Description Enrichment

The base description from `A2A_DESCRIPTION` is dynamically enriched with:
- Number of discovered skills
- Configured model name (from `config.toml`)
- Number of configured MCP servers (from `config.toml`)
- Number of installed plugins

## Filesystem Sources

| Data | File | Format |
|---|---|---|
| Skills | `*/SKILL.md` | YAML frontmatter (name, description, metadata) |
| Skill UI metadata | `*/agents/openai.yaml` | YAML (interface.display_name, short_description, default_prompt) |
| Model/provider | `config.toml` | TOML (model, model_provider keys) |
| MCP servers | `config.toml` | TOML (`[mcp_servers.*]` sections) |
| Plugins | `.codex-plugin/plugin.json` | JSON manifest |
