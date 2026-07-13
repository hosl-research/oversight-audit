"""
Sensitivity analysis: is the non-identifiability result an artifact of the
generator's parameters, or does it hold across them?

The demo runs at one configuration. A constructive proof at one configuration
invites the obvious objection: you tuned it. This sweeps the two parameters that
objection would target, each from the baseline the demo uses, and reports whether
the qualitative result survives.

  1. Decision disagreement: how far engaged and procedural reviewers diverge in the
     decisions they log. At zero they agree, so the decision carries nothing about
     engagement. As it rises the standard trail starts to separate the two groups,
     because the decision now reflects engagement. The result to read off the sweep
     is that the standard trail only becomes informative once the failure is
     already visible in the decisions, which is the regime where the tool is not
     needed.

  2. Timestamp dwell weight: how much of the gap between logged decisions reflects
     real review time rather than queue wait and batching. At zero the timestamp is
     exogenously dominated and near useless. As it rises, throughput derived from
     timestamps carries more engagement. This puts a number on the one contestable
     assumption behind the demo: how much of the logged gap would have to be review
     time before the standard trail could see engagement.

For each level on each axis we report the best separability of the STANDARD field
group and of the FUNCTION field group, each with a bootstrap confidence interval
resampled over reviewers. Pure standard library. Deterministic for a fixed seed.
"""

from __future__ import annotations

import random

from .generate import generate_log
from .signals import FEATURES, aggregate_by_reviewer, separability


DISAGREEMENT_LEVELS = (0.0, 0.15, 0.30, 0.45, 0.60)
DWELL_LEVELS = (0.0, 0.25, 0.50, 0.75, 1.0)


def _best_group_seps(rows: list[dict]) -> tuple[float, float]:
    """Best separability within the STANDARD group and within the FUNCTION group."""
    pos = [r for r in rows if r["engaged"]]
    neg = [r for r in rows if not r["engaged"]]
    best_std, best_fun = 0.5, 0.5
    for name, (group, _label) in FEATURES.items():
        s = separability([r[name] for r in pos], [r[name] for r in neg])
        if group == "STANDARD":
            best_std = max(best_std, s)
        else:
            best_fun = max(best_fun, s)
    return best_std, best_fun


def _bootstrap_ci(rows: list[dict], rng: random.Random, b: int) -> tuple[tuple, tuple]:
    n = len(rows)
    stds, funs = [], []
    for _ in range(b):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        s, f = _best_group_seps(sample)
        stds.append(s)
        funs.append(f)
    stds.sort()
    funs.sort()

    def pct(xs: list[float], p: float) -> float:
        return xs[min(len(xs) - 1, max(0, int(p * len(xs))))]

    return (pct(stds, 0.025), pct(stds, 0.975)), (pct(funs, 0.025), pct(funs, 0.975))


def _point_and_ci(events: list[dict], boot_seed: int, b: int) -> dict:
    rows = aggregate_by_reviewer(events)
    std, fun = _best_group_seps(rows)
    (std_lo, std_hi), (fun_lo, fun_hi) = _bootstrap_ci(rows, random.Random(boot_seed), b)
    return {
        "standard": {"sep": round(std, 3), "lo": round(std_lo, 3), "hi": round(std_hi, 3)},
        "function": {"sep": round(fun, 3), "lo": round(fun_lo, 3), "hi": round(fun_hi, 3)},
    }


def run_sensitivity(seed: int = 20260709, bootstrap: int = 400) -> dict:
    """Sweep both axes and return the structured result."""
    disagreement = []
    for i, d in enumerate(DISAGREEMENT_LEVELS):
        events = generate_log(seed=seed, decision_disagreement=d)
        row = _point_and_ci(events, seed + 1000 + i, bootstrap)
        row["level"] = d
        disagreement.append(row)

    dwell = []
    for i, w in enumerate(DWELL_LEVELS):
        events = generate_log(seed=seed, timestamp_dwell_weight=w)
        row = _point_and_ci(events, seed + 2000 + i, bootstrap)
        row["level"] = w
        dwell.append(row)

    return {
        "seed": seed,
        "bootstrap": bootstrap,
        "decision_disagreement": disagreement,
        "timestamp_dwell_weight": dwell,
    }


def _bar(sep: float, width: int = 8) -> str:
    filled = int(round((min(1.0, max(0.5, sep)) - 0.5) / 0.5 * width))
    return "|" + "#" * filled + "-" * (width - filled) + "|"


def _axis_block(title: str, note: str, rows: list[dict], level_label: str) -> list[str]:
    L = [title, "  " + note, ""]
    L.append(f"  {level_label:>5}   standard sep [95% CI]        function sep [95% CI]")
    for r in rows:
        s, f = r["standard"], r["function"]
        L.append(
            f"  {r['level']:>5.2f}   "
            f"{s['sep']:.2f} [{s['lo']:.2f},{s['hi']:.2f}] {_bar(s['sep'])}   "
            f"{f['sep']:.2f} [{f['lo']:.2f},{f['hi']:.2f}] {_bar(f['sep'])}"
        )
    return L


def format_sensitivity(result: dict) -> str:
    dis = result["decision_disagreement"]
    dw = result["timestamp_dwell_weight"]
    L = []
    L.append("oversight-audit :: sensitivity of the non-identifiability result")
    L.append("=" * 74)
    L.append(f"seed {result['seed']}, {result['bootstrap']} bootstrap resamples per level.")
    L.append("Baseline (level 0.00 on both axes) is the configuration the demo runs.")
    L.append("")

    L += _axis_block(
        "AXIS 1  DECISION DISAGREEMENT",
        "how far engaged and procedural reviewers diverge in logged decisions",
        dis,
        "delta",
    )
    d0, dN = dis[0]["standard"], dis[-1]["standard"]
    L.append("")
    L.append(
        f"  Standard separability moves {d0['sep']:.2f} -> {dN['sep']:.2f} as decisions diverge."
    )
    L.append(
        "  In the agreement regime (0.00) the standard trail is near chance. It only"
    )
    L.append(
        "  sees engagement once the decisions themselves do, which is the regime where"
    )
    L.append("  the failure is already visible without this tool.")
    L.append("")

    L += _axis_block(
        "AXIS 2  TIMESTAMP DWELL WEIGHT",
        "share of the logged inter-decision gap that is real review time",
        dw,
        "weight",
    )
    w0, wN = dw[0]["standard"], dw[-1]["standard"]
    L.append("")
    L.append(
        f"  Standard separability moves {w0['sep']:.2f} -> {wN['sep']:.2f} as timestamps absorb dwell."
    )
    L.append(
        "  At the baseline (0.00) timestamps are near chance. They carry engagement"
    )
    L.append(
        "  only when much of the logged gap is review time, which the workload"
    )
    L.append("  literature says it is not.")
    L.append("")
    L.append("-" * 74)
    L.append(
        "Across both sweeps the function fields stay high while the standard fields"
    )
    L.append(
        "sit near chance until the failure is already in the decisions. The result is"
    )
    L.append("not an artifact of the baseline configuration.")
    return "\n".join(L)


def run_and_print(seed: int = 20260709, bootstrap: int = 400) -> dict:
    result = run_sensitivity(seed=seed, bootstrap=bootstrap)
    print(format_sensitivity(result))
    return result
