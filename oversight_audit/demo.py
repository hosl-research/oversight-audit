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


def format_demo(report: dict) -> str:
    lines = []
    lines.append("oversight-audit :: the identity demonstration")
    lines.append("=" * 60)
    lines.append(
        f"{report['n_reviewers']} reviewers "
        f"({report['n_engaged']} engaged, {report['n_procedural']} procedural), "
        "known ground truth."
    )
    lines.append("")
    lines.append("How well does each field separate engaged from procedural?")
    lines.append("  0.50 = chance (the field carries no information)")
    lines.append("  1.00 = perfect")
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

    section("In a standard audit trail (decision, approval, timestamps):", "STANDARD")
    section("Requires added instrumentation (not in a standard trail):", "FUNCTION")

    bs, bf = report["best_standard"], report["best_function"]
    lines.append("-" * 60)
    lines.append(
        f"Best a standard trail can do: {bs:.2f}. "
        f"Best with function-level signals: {bf:.2f}."
    )
    lines.append("")
    lines.append(
        "The two populations did opposite things. On the record you keep, they are "
        "nearly indistinguishable. The separation lives entirely in fields a standard "
        "audit trail does not keep. That is the gap: your record certifies that review "
        "happened, not that it worked."
    )
    return "\n".join(lines)


def run_demo(seed: int = 20260709) -> dict:
    events = generate_log(seed=seed)
    report = separability_report(events)
    print(format_demo(report))
    return report
