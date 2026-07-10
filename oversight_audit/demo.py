"""
The identity demonstration, printed to the terminal.

Generates two populations of reviewers with known ground truth and shows the
contrast: the fields a standard audit trail keeps separate engaged from
procedural reviewers at close to chance, while function-level signals separate
them cleanly. The record you keep cannot see the difference; the record you would
have to instrument can.
"""

from __future__ import annotations

from .generate import generate_log
from .signals import separability_report


def _bar(sep: float, width: int = 24) -> str:
    # map separability in [0.5, 1.0] to a bar
    frac = max(0.0, min(1.0, (sep - 0.5) / 0.5))
    filled = round(frac * width)
    return "#" * filled + "-" * (width - filled)


_RULE = "=" * 76
_THIN = "-" * 76


def format_demo(report: dict) -> str:
    lines = []
    lines.append("oversight-audit :: can your record tell careful review from rubber-stamping?")
    lines.append(_RULE)
    lines.append(
        f"{report['n_reviewers']} reviewers "
        f"({report['n_engaged']} engaged, {report['n_procedural']} procedural). "
        "Same task. Same decision mix."
    )
    lines.append("Ground truth is known here. In a real audit it never is.")
    lines.append("")
    lines.append("Score: how well each field separates engaged from procedural reviewers.")
    lines.append("  0.50 = chance (the field tells you nothing)      1.00 = perfect")
    lines.append("")

    def section(title: str, group: str) -> None:
        lines.append(title)
        for f in report["fields"]:
            if f["group"] != group:
                continue
            lines.append(
                f"  {f['separability']:.2f}  |{_bar(f['separability'])}|  {f['label']}"
            )
        lines.append("")

    section("WHAT A STANDARD AUDIT TRAIL KEEPS  (decision, approval, timestamps)", "STANDARD")
    section("WHAT IT DOES NOT KEEP  (requires added instrumentation)", "FUNCTION")

    bs, bf = report["best_standard"], report["best_function"]
    lines.append(_THIN)
    lines.append(
        f"Best your audit trail can do: {bs:.2f}.    "
        f"Best with the fields it drops: {bf:.2f}."
    )
    lines.append("")
    lines.append(
        "Two populations that did opposite things. Nearly identical on the record you keep."
    )
    lines.append("Your record certifies that review happened, not that it worked.")
    return "\n".join(lines)


def run_demo(seed: int = 20260709) -> dict:
    events = generate_log(seed=seed)
    report = separability_report(events)
    print(format_demo(report))
    return report
