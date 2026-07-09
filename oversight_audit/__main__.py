"""
Command line entry point.

    python -m oversight_audit demo
    python -m oversight_audit check examples/typical_audit_schema.json
    python -m oversight_audit generate --out mylog.json
"""

from __future__ import annotations

import argparse
import json
import sys

from .demo import run_demo
from .generate import generate_log
from .schema_audit import audit_schema


def _format_check(result: dict, schema_name: str) -> str:
    lines = []
    lines.append(f"oversight-audit :: instrumentation self-audit ({schema_name})")
    lines.append("=" * 60)
    lines.append(f"Recognized fields: {', '.join(result['recognized_fields']) or '(none)'}")
    lines.append("")
    lines.append("Function-level oversight signals:")
    for s in result["signals"]:
        mark = "YES" if s["computable"] else "NO "
        lines.append(f"  [{mark}] {s['question']}")
        if not s["computable"]:
            needs = []
            if s["missing_required"]:
                needs.append("add " + ", ".join(s["missing_required"]))
            for group in s["missing_one_of"]:
                needs.append("add one of {" + ", ".join(group) + "}")
            lines.append(f"        to compute: {'; '.join(needs)}")
    lines.append("")
    lines.append(
        f"Computable: {result['computable_count']} of {result['total_signals']}."
    )
    lines.append("")
    lines.append("Verdict:")
    for chunk in _wrap(result["verdict"], 58):
        lines.append("  " + chunk)
    return "\n".join(lines)


def _wrap(text: str, width: int) -> list[str]:
    words, line, out = text.split(), "", []
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="oversight-audit",
        description="Does your AI-review logging record process, or function?",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("demo", help="run the identity demonstration on synthetic data")
    d.add_argument("--seed", type=int, default=20260709)

    c = sub.add_parser("check", help="audit a review-log schema (JSON) for signal coverage")
    c.add_argument("schema", help="path to a schema JSON: {\"name\":..., \"fields\":[...]}")

    g = sub.add_parser("generate", help="write a synthetic review log to JSON")
    g.add_argument("--out", default="-", help="output path, or - for stdout")
    g.add_argument("--seed", type=int, default=20260709)

    args = parser.parse_args(argv)

    if args.command == "demo":
        run_demo(seed=args.seed)
        return 0

    if args.command == "check":
        with open(args.schema, encoding="utf-8") as fh:
            schema = json.load(fh)
        fields = schema.get("fields", [])
        if not isinstance(fields, list):
            print("schema 'fields' must be a list of field names", file=sys.stderr)
            return 2
        result = audit_schema(fields)
        print(_format_check(result, schema.get("name", args.schema)))
        return 0

    if args.command == "generate":
        events = generate_log(seed=args.seed)
        text = json.dumps(events, indent=2)
        if args.out == "-":
            print(text)
        else:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"wrote {len(events)} events to {args.out}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
