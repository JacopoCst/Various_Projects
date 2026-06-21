---
name: headroom-compress
description: >-
  Measure and apply Headroom token compression to STRUCTURED payloads (JSON
  arrays of records, tabular tool/API output, dataset slices) before sending
  them to an LLM. Use when a prompt/context is dominated by repetitive
  structured data and you want to cut token cost, or when the user asks to
  benchmark/estimate compression savings on a file. Do NOT use for raw prose or
  free text — it does not compress without the optional ML model.
---

# headroom-compress

A thin, honest wrapper around [`headroom-ai`](https://github.com/chopratejas/headroom)
for compressing **structured** payloads before they reach an LLM.

## When this helps (measured, lossless)

Headroom's `SmartCrusher` rewrites repetitive JSON (arrays of records with
repeated keys) into a compact schema-header + CSV-style rows. All data is
preserved — it is a denser encoding, not a summary — so there is **no accuracy
risk**. Measured savings on structured data: **~65–90%**.

Good fits:
- JSON arrays of records (dataset slices, e.g. news/tweet rows, DB query results)
- Tool / API output with many similar objects
- Code-search results, structured log records

## When this does NOT help

- **Raw prose / free text** → ~0% savings here. The general-text path needs the
  optional `Kompress-base` HuggingFace model, which is not enabled by default.
- A single small payload (< ~250 tokens) — below Headroom's compression floor.
- Content already sent through a provider's native compaction.

**Always benchmark first.** If `benchmark` reports < ~5%, the payload is not a fit.

## Setup

```bash
pip install headroom-ai
```

## Usage

The helper lives in `scripts/hr.py`.

Measure savings before trusting it (local only, makes no LLM call):

```bash
python3 .claude/skills/headroom-compress/scripts/hr.py benchmark data/records.json
# multiple files compared side by side:
python3 .claude/skills/headroom-compress/scripts/hr.py benchmark a.json b.json c.txt
```

Apply compression and write the dense payload to a file (or stdout):

```bash
python3 .claude/skills/headroom-compress/scripts/hr.py compress data/records.json --out out.txt
```

Then send `out.txt` as the payload to the model in place of the original.

## Notes

- The helper presents the payload as a **tool result** internally, because
  Headroom's default config compresses tool/assistant context and protects the
  most recent user turn. This is why you pass the raw data file directly.
- Token counts use the `claude-sonnet-4-5` tokenizer for sizing; savings ratios
  are essentially model-agnostic.
- This skill is scoped to structured-data compression. Wrapping the coding agent
  itself (`headroom wrap claude|codex`) is a separate setup and intentionally
  out of scope here.
