"""
Command line entry point.

    python -m oversight_audit demo
    python -m oversight_audit check examples/typical_audit_schema.json
    python -m oversight_audit estimate mylog.json
    python -m oversight_audit generate --out mylog.json
"""

from __future__ import annotations

import argparse
import json
import sys

from .demo import run_demo
from .reveal import run_reveal
from .sensitivity import run_sensitivity, format_sensitivity
from .generate import generate_log
from .schema_audit import audit_schema
from .estimate import estimate_log, format_estimate


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

    r = sub.add_parser("reveal", help="six individual records: guess who looked, then see the truth")
    r.add_argument("--seed", type=int, default=20260709)

    s = sub.add_parser("sensitivity", help="sweep two axes; show the result is not a tuned artifact")
    s.add_argument("--seed", type=int, default=20260709)
    s.add_argument("--bootstrap", type=int, default=400, help="bootstrap resamples per level")
    s.add_argument("--json", action="store_true", help="emit the raw result as JSON")

    c = sub.add_parser("check", help="audit a review-log schema (JSON) for signal coverage")
    c.add_argument("schema", help="path to a schema JSON: {\"name\":..., \"fields\":[...]}")

    e = sub.add_parser(
        "estimate",
        help="bound how much engagement a real log's timestamps could carry",
    )
    e.add_argument("log", help="path to a JSON list of events with reviewer id + timestamp")
    e.add_argument("--burst-floor", type=float, default=5.0,
                   help="gaps shorter than this (s) cannot contain review (default 5)")
    e.add_argument("--break-ceiling", type=float, default=1800.0,
                   help="gaps longer than this (s) are breaks (default 1800)")
    e.add_argument("--max-review", type=float, default=600.0,
                   help="max plausible review time per item (s) (default 600)")
    e.add_argument("--json", action="store_true", help="emit the raw result as JSON")

    g = sub.add_parser("generate", help="write a synthetic review log to JSON")
    g.add_argument("--out", default="-", help="output path, or - for stdout")
    g.add_argument("--seed", type=int, default=20260709)

    args = parser.parse_args(argv)

    if args.command == "demo":
        run_demo(seed=args.seed)
        return 0

    if args.command == "reveal":
        run_reveal(seed=args.seed)
        return 0

    if args.command == "sensitivity":
        result = run_sensitivity(seed=args.seed, bootstrap=args.bootstrap)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_sensitivity(result))
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

    if args.command == "estimate":
        with open(args.log, encoding="utf-8") as fh:
            events = json.load(fh)
        if not isinstance(events, list):
            print("log must be a JSON list of event objects", file=sys.stderr)
            return 2
        try:
            result = estimate_log(
                events,
                burst_floor_s=args.burst_floor,
                break_ceiling_s=args.break_ceiling,
                max_review_s=args.max_review,
            )
        except ValueError as err:
            print(f"estimate: {err}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_estimate(result))
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
