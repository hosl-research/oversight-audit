"""
Instrumentation self-audit.

You describe the schema of your review log -- the fields you actually capture --
and this reports which function-level oversight signals you can and cannot compute
from it. It does not read your data and it does not claim to detect rubber-stamping.
It tells you whether your logging is even capable of the distinction: what would
change in your record if a reviewer stopped looking?

A schema is a JSON object: {"name": "...", "fields": ["reviewer_id", ...]}.
"""

from __future__ import annotations


# Canonical field names, with a few forgiving aliases mapped onto them.
_ALIASES = {
    "timestamp": "decision_timestamp",
    "reviewed_at": "decision_timestamp",
    "decided_at": "decision_timestamp",
    "dwell_time": "time_on_item",
    "time_on_item_s": "time_on_item",
    "time_spent": "time_on_item",
    "evidence_views": "evidence_opened",
    "evidence_expanded": "evidence_opened",
    "corrections": "correction_count",
    "num_corrections": "correction_count",
    "rationale_specificity": "correction_specificity",
    "accepted_without_change": "accepted_unmodified",
    "unmodified_accept": "accepted_unmodified",
    "items_shown": "items_presented_count",
    "queue_volume": "items_presented_count",
    "presented_at": "item_presented_timestamp",
}


def _normalize(fields: list[str]) -> set[str]:
    out = set()
    for f in fields:
        key = f.strip().lower()
        out.add(_ALIASES.get(key, key))
    return out


# Each signal: requires_all (every field needed) and requires_any (a list of
# OR-groups; at least one field from each group must be present).
SIGNALS = {
    "substantive_vs_procedural": {
        "question": "Can a substantive review be told apart from a procedural one?",
        "requires_all": [],
        "requires_any": [["evidence_opened", "time_on_item", "correction_specificity"]],
        "why": (
            "Distinguishing engagement needs at least one field that records what the "
            "reviewer did, not just what they decided: whether they opened the evidence, "
            "how long they spent on the item, or how specific their rationale was."
        ),
    },
    "correction_rate_trajectory": {
        "question": "Is the correction rate drifting down over time?",
        "requires_all": ["correction_count", "decision_timestamp"],
        "requires_any": [],
        "why": (
            "A falling correction rate over time is an early sign scrutiny is thinning. "
            "It needs per-item correction counts ordered by time."
        ),
    },
    "validation_load_vs_volume": {
        "question": "Is reviewer capacity being outpaced by output volume?",
        "requires_all": ["decision_timestamp"],
        "requires_any": [["items_presented_count", "item_presented_timestamp"]],
        "why": (
            "Load relative to volume shows when review is being rushed by throughput. "
            "It needs decision timing plus a measure of how much was presented."
        ),
    },
    "dependency_accumulation": {
        "question": "Is reliance on unmodified AI output growing?",
        "requires_all": ["accepted_unmodified", "decision_timestamp"],
        "requires_any": [],
        "why": (
            "Growing accept-without-change over time is accumulating dependence on "
            "unverified output. It needs an unmodified-accept marker ordered by time."
        ),
    },
}


def audit_schema(fields: list[str]) -> dict:
    present = _normalize(fields)
    results = []
    for sid, spec in SIGNALS.items():
        missing_all = [f for f in spec["requires_all"] if f not in present]
        missing_groups = []
        for group in spec["requires_any"]:
            if not any(f in present for f in group):
                missing_groups.append(group)
        computable = not missing_all and not missing_groups
        results.append(
            {
                "signal": sid,
                "question": spec["question"],
                "computable": computable,
                "missing_required": missing_all,
                "missing_one_of": missing_groups,
                "why": spec["why"],
            }
        )
    n_ok = sum(1 for r in results if r["computable"])
    return {
        "recognized_fields": sorted(present),
        "signals": results,
        "computable_count": n_ok,
        "total_signals": len(results),
        "verdict": _verdict(n_ok, len(results)),
    }


def _verdict(n_ok: int, total: int) -> str:
    if n_ok == 0:
        return (
            "Your record cannot distinguish substantive review from procedural review. "
            "Nothing in it would change if a reviewer stopped looking. Oversight is "
            "logged but unverifiable."
        )
    if n_ok < total:
        return (
            f"You can compute {n_ok} of {total} function-level signals. Some of the "
            "difference between substantive and procedural review is visible to you; "
            "the rest is not yet instrumented."
        )
    return (
        "You can compute all function-level signals defined here. Your logging is "
        "capable of asking whether oversight is working, not just that it happened. "
        "These signals are a starting agenda, not a finished control set."
    )
