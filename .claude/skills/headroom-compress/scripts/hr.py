#!/usr/bin/env python3
"""hr.py - Headroom structured-payload compression utility.

Two subcommands:

    benchmark <file> [<file> ...]   A/B measure token savings (no LLM call, local)
    compress  <file> [--out OUT]    Write the compressed payload to OUT (or stdout)

Headroom compresses content losslessly when it is *structured and repetitive*
(JSON arrays of records, tabular tool/API output). It does NOT compress raw
prose/free text unless the optional Kompress-base ML model is configured.
Use `benchmark` first: if savings are near 0%, the payload is not a fit.

Requires: pip install headroom-ai
"""
import argparse
import json
import sys
from pathlib import Path

# Default model used only for token counting + context-window sizing.
MODEL = "claude-sonnet-4-5-20250929"


def _require_headroom():
    try:
        import headroom  # noqa: F401
        return headroom
    except ImportError:
        sys.exit("headroom-ai is not installed. Run: pip install headroom-ai")


def _wrap_as_tool_output(content: str) -> list[dict]:
    """Headroom's default config compresses tool/assistant context, not the
    last user turn. We present the payload as a tool result so the structured
    compressors (SmartCrusher etc.) actually run on it."""
    return [
        {"role": "user", "content": "Process the data returned by the tool."},
        {"role": "assistant", "content": "Calling the tool to fetch the data."},
        {"role": "tool", "content": content},
        {"role": "assistant", "content": "Data received."},
        {"role": "user", "content": "Continue."},
    ]


def _compressed_payload(headroom, content: str):
    """Return (result, compressed_tool_message_content)."""
    msgs = _wrap_as_tool_output(content)
    res = headroom.compress(msgs, model=MODEL)
    comp = res.messages[2]["content"]
    if not isinstance(comp, str):
        comp = json.dumps(comp, ensure_ascii=False)
    return res, comp


def cmd_benchmark(args):
    headroom = _require_headroom()
    rows = []
    tot_b = tot_a = 0
    for f in args.files:
        content = Path(f).read_text(encoding="utf-8", errors="replace")
        res, _ = _compressed_payload(headroom, content)
        saved = res.tokens_before - res.tokens_after
        pct = 100 * saved / res.tokens_before if res.tokens_before else 0.0
        tot_b += res.tokens_before
        tot_a += res.tokens_after
        rows.append((f, res.tokens_before, res.tokens_after, saved, pct))

    name_w = max([len("File")] + [len(r[0]) for r in rows])
    print(f"{'File':<{name_w}}{'before':>10}{'after':>10}{'saved':>10}{'ratio':>9}")
    print("-" * (name_w + 39))
    for f, b, a, s, p in rows:
        print(f"{f:<{name_w}}{b:>10}{a:>10}{s:>10}{p:>8.1f}%")
    if len(rows) > 1:
        tot_s = tot_b - tot_a
        tot_p = 100 * tot_s / tot_b if tot_b else 0.0
        print("-" * (name_w + 39))
        print(f"{'TOTAL':<{name_w}}{tot_b:>10}{tot_a:>10}{tot_s:>10}{tot_p:>8.1f}%")
    worst = min(r[4] for r in rows)
    if worst < 5:
        print("\nNote: <5% savings on some inputs -> likely raw prose / unstructured "
              "text. Headroom is not a fit for those without the Kompress-base model.")


def cmd_compress(args):
    headroom = _require_headroom()
    content = Path(args.file).read_text(encoding="utf-8", errors="replace")
    res, comp = _compressed_payload(headroom, content)
    saved = res.tokens_before - res.tokens_after
    pct = 100 * saved / res.tokens_before if res.tokens_before else 0.0
    if args.out:
        Path(args.out).write_text(comp, encoding="utf-8")
        print(f"Wrote {args.out}: {res.tokens_before} -> {res.tokens_after} tokens "
              f"({pct:.1f}% saved)", file=sys.stderr)
    else:
        sys.stdout.write(comp)
        print(f"\n[{res.tokens_before} -> {res.tokens_after} tokens, {pct:.1f}% saved]",
              file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description="Headroom structured-payload compression utility.")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("benchmark", help="A/B measure token savings (local, no LLM call)")
    b.add_argument("files", nargs="+", help="One or more files to measure")
    b.set_defaults(func=cmd_benchmark)

    c = sub.add_parser("compress", help="Compress a payload file")
    c.add_argument("file", help="File to compress")
    c.add_argument("--out", help="Output path (default: stdout)")
    c.set_defaults(func=cmd_compress)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
