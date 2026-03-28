# Enrich MCP

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that acts as an **AI Architect** enrichment layer on top of code graph data. It takes raw output from a code graph tool (e.g. codegraph), analyzes it using an AI model, and returns a structured architectural breakdown with a concise, token-efficient summary — so your AI coding assistant can write accurate code without hallucinating.

## What does it do?

Exposes a single MCP tool:

```
enrich_architectural_context(raw_codegraph_data: str, target_focus: str) -> str
```

Pass in raw codegraph output and a focus (function name, file, or feature). The tool sends it to your chosen AI provider and returns two XML-tagged sections:

- **`<pre_thinking>`** — architectural breakdown: data flow, state mutations, key dependencies, and "gotchas".
- **`<distilled_context>`** — a concise markdown summary with exact signatures, DTOs, and caller contexts ready for use by a coding assistant.

Supports two AI providers: **Anthropic** (default) and **GitHub Copilot**.

---

## Getting Started

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Export these variables in your shell:

| Variable            | Example             | Description                                                           |
| ------------------- | ------------------- | --------------------------------------------------------------------- |
| `ENRICHER_PROVIDER` | `anthropic`         | AI provider to use: `anthropic` or `copilot`                          |
| `MAX_OUTPUT_TOKENS` | `4096`              | Maximum tokens in the AI response                                     |
| `COPILOT_MODEL`     | `claude-sonnet-4.6` | Model name when using the Copilot provider                            |
| `ANTHROPIC_MODEL`   | `claude-opus-4-6`   | Model name when using the Anthropic provider                          |
| `ANTHROPIC_API_KEY` | `sk-ant-abc123...`  | Your Anthropic API key, only required if using the Anthropic provider |

Default values (hardcoded in `enrich_mcp.py`):

```bash
export ENRICHER_PROVIDER=anthropic
export MAX_OUTPUT_TOKENS=4096
export COPILOT_MODEL=claude-sonnet-4.5
export ANTHROPIC_MODEL=claude-haiku-4-5
```

---

## Starting the MCP Server

```bash
python enrich_mcp.py
```

Example of Github Copilot CLI MCP configuration `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "enricher": {
      "type": "local",
      "command": "/path/to/enrich_mcp/.venv/bin/python",
      "args": ["/path/to/enrich_mcp/enrich_mcp.py"],
      "tools": ["*"],
      "env": {
        "ENRICHER_PROVIDER": "copilot", // or "anthropic"
        "MAX_OUTPUT_TOKENS": "4096",
        "COPILOT_MODEL": "claude-sonnet-4.5",
        "ANTHROPIC_MODEL": "claude-haiku-4-5",
        "ANTHROPIC_API_KEY": "sk-ant-abc123..."
      }
    }
  }
}
```

The server communicates over **stdio** (standard MCP transport). Register it in your MCP host (e.g. Claude Desktop, VS Code) pointing to this command.

To test the server end-to-end, put sample payload into `sample/mcp_input_sample.json`:

```json
{
  "raw_codegraph_data": "function foo(...args) { ... }",
  "target_focus": "Callers of foo() and the data they pass in"
}
```

And then, run the test script:

```bash
cd /path/to/enrich_mcp
python -m scripts.enrich_test
```

If the server is running and properly configured, you should see the enriched architectural context printed in the console.

---

## GitHub Copilot Provider

### Login / Obtain a Token

When `ENRICHER_PROVIDER=copilot`, the server needs a GitHub OAuth token. Run the login script once to authenticate via GitHub Device Flow:

```bash
cd /path/to/enrich_mcp
python -m scripts.copilot_login
```

Follow the printed instructions — visit the URL and enter the device code in your browser. The token is saved to `~/.config/enrich_mcp/oauth_token.json` and reused on subsequent runs.

> **Note:** If you already have GitHub Copilot authenticated in VS Code, the token at `~/.config/github-copilot/hosts.json` is picked up automatically — no login step needed.

---

## Anthropic Provider

Set `ENRICHER_PROVIDER=anthropic` (the default) and provide your Anthropic API key via the environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

The `AsyncAnthropic` client picks up `ANTHROPIC_API_KEY` automatically.
