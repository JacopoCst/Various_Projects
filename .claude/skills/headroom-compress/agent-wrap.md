# Wrapping the coding agent through Headroom (optional)

This is the **separate** integration from the structured-data utility in `SKILL.md`.
It routes a coding agent's traffic (Claude Code, Codex, …) through Headroom's
proxy so tool outputs / file dumps are compressed automatically during a session,
with CCR retrieval for anything the model needs in full.

> Run this on your **local machine** where you use the agent — not inside a
> sandboxed/remote container (the proxy needs a local process plus network
> egress to the provider API).

## Install (proxy extras required)

```bash
pip install 'headroom-ai[proxy]'
```

## Option A — durable integration (recommended)

Installs persistent hooks + provider routing for the agent:

```bash
headroom init claude   --backend anthropic     # Claude Code
headroom init codex                            # OpenAI Codex
# undo with: headroom unwrap
```

## Option B — one-shot wrap

Starts the proxy, sets env vars, and launches the tool for that session:

```bash
headroom wrap claude
headroom wrap codex
```

## Option C — manual proxy

```bash
headroom proxy --port 8787 --backend anthropic        # terminal 1
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude        # terminal 2
```

## CCR retrieval (subscription users without API access)

```bash
headroom mcp install     # adds mcp__headroom__headroom_retrieve to Claude Code
```

Then the model sees compressed tool outputs with hash markers and calls
`headroom_retrieve` only when it needs the original.

## Verified in this environment / caveats

- `headroom proxy` boots and serves `/health` (200, `status: healthy`). ✅
- Provider egress to `api.anthropic.com` works (401 without a key, as expected). ✅
- **Use `--backend anthropic` for Claude Code.** The proxy's default backend
  probes `api.openai.com`; if that host is outside your network allowlist the
  `/` and `/v1/models` routes return 403. ⚠️
- A full authenticated round-trip was **not** tested here (no API key in this
  container). Validate cost savings locally with `headroom perf` / the
  `agent-savings` command on a real session before relying on the numbers.
- The Kompress-base ML model (general-text compression) auto-downloads from
  HuggingFace on first use; if HF egress is blocked it falls back to passthrough
  (no error, but no prose compression). Structured tool output still compresses.
