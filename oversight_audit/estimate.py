"""
Test the timing assumption on a real log.

The non-identifiability argument leans on one empirical premise: that the gap
between two logged decisions contains almost no review time, because queue wait,
batching, context switching, and breaks dominate it. The sensitivity sweep shows
the premise is load-bearing -- at a dwell share of just 0.25 the standard trail
begins to separate engaged from procedural reviewers.

This module bounds that dwell share for a real log. Given events with a reviewer
id and a decision timestamp, it decomposes each reviewer's inter-decision gaps:

  - bursts:  gaps too short to contain review (batched or scripted logging);
  - breaks:  gaps too long to be one item's review (the reviewer walked away);
  - working: gaps in between, which could be review, or could be anything else.

It then reports an UPPER BOUND on the share of logged gap time that could be
review: per gap, dwell is at most min(gap, max_review), and zero inside a burst.

The bound is asymmetric by design, and the asymmetry is the honesty:

  - A LOW bound exonerates the timestamps. Burst- and break-dominated gaps
    provably cannot carry much engagement, the timing premise holds, and the
    non-identifiability argument applies to this log with force.
  - A HIGH bound convicts nothing. It says the gaps COULD contain review time;
    whether they do is unknowable from timestamps alone. Running this on the
    synthetic `generate` output returns a high bound even though the true dwell
    weight there is zero by construction. That is the bound working as designed.

Pure standard library.
"""

from __future__ import annotations

from datetime import datetime


# Accepted key aliases for the two required event fields.
_REVIEWER_KEYS = ("reviewer_id", "reviewer", "approver", "user_id", "actor")
_TIMESTAMP_KEYS = (
    "decision_timestamp",
    "timestamp",
    "decided_at",
    "reviewed_at",
    "logged_at",
    "created_at",
)

# The sweep level at which the standard trail reaches ~0.81 separability
# (seed 20260709); the reference point the verdict compares the bound against.
SWEEP_INFORMATIVE_DWELL = 0.25


def _find_key(event: dict, candidates: tuple[str, ...], what: str) -> str:
    for k in candidates:
        if k in event:
            return k
    raise ValueError(
        f"could not find a {what} field; looked for one of: {', '.join(candidates)}"
    )


def _to_seconds(value) -> float:
    """Accept numeric epoch seconds or an ISO-8601 timestamp string."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    raise ValueError(f"cannot interpret timestamp value: {value!r}")


def estimate_log(
    events: list[dict],
    burst_floor_s: float = 5.0,
    break_ceiling_s: float = 1800.0,
    max_review_s: float = 600.0,
) -> dict:
    """
    Decompose inter-decision gaps and bound the dwell share of logged gap time.

    Returns a dict with gap composition (by count and by time) and
    `dwell_share_upper_bound`, the fraction of total gap time that could be
    review under the most generous reading of the timestamps.
    """
    if not events:
        raise ValueError("log is empty")
    rk = _find_key(events[0], _REVIEWER_KEYS, "reviewer id")
    tk = _find_key(events[0], _TIMESTAMP_KEYS, "decision timestamp")

    by_rev: dict[str, list[float]] = {}
    for e in events:
        by_rev.setdefault(str(e[rk]), []).append(_to_seconds(e[tk]))

    gaps: list[float] = []
    for times in by_rev.values():
        times.sort()
        gaps.extend(b - a for a, b in zip(times, times[1:]))

    if not gaps:
        raise ValueError(
            "no inter-decision gaps: every reviewer has a single event. "
            "The gap analysis needs at least one reviewer with two or more decisions."
        )

    burst = [g for g in gaps if g < burst_floor_s]
    brk = [g for g in gaps if g > break_ceiling_s]
    work = [g for g in gaps if burst_floor_s <= g <= break_ceiling_s]

    total_time = sum(gaps)
    # Upper bound: no review fits inside a burst; elsewhere dwell <= min(gap, max_review).
    dwell_max = sum(min(g, max_review_s) for g in gaps if g >= burst_floor_s)
    bound = (dwell_max / total_time) if total_time > 0 else 0.0

    def _share(xs: list[float]) -> dict:
        return {
            "count": len(xs),
            "count_share": round(len(xs) / len(gaps), 3),
            "time_share": round((sum(xs) / total_time) if total_time else 0.0, 3),
        }

    return {
        "n_events": len(events),
        "n_reviewers": len(by_rev),
        "n_gaps": len(gaps),
        "reviewer_field": rk,
        "timestamp_field": tk,
        "params": {
            "burst_floor_s": burst_floor_s,
            "break_ceiling_s": break_ceiling_s,
            "max_review_s": max_review_s,
        },
        "bursts": _share(burst),
        "working": _share(work),
        "breaks": _share(brk),
        "dwell_share_upper_bound": round(bound, 3),
        "premise_holds": bound < SWEEP_INFORMATIVE_DWELL,
    }


def format_estimate(result: dict) -> str:
    p = result["params"]
    bound = result["dwell_share_upper_bound"]
    L = []
    L.append("oversight-audit :: could your timestamps carry engagement?")
    L.append("=" * 68)
    L.append(
        f"{result['n_events']} events, {result['n_reviewers']} reviewers, "
        f"{result['n_gaps']} inter-decision gaps "
        f"(fields: {result['reviewer_field']}, {result['timestamp_field']})."
    )
    L.append("")
    L.append("Gap composition (share of gaps / share of gap time):")
    L.append(
        f"  bursts   < {p['burst_floor_s']:>6.0f}s   "
        f"{result['bursts']['count_share']:>5.0%} / {result['bursts']['time_share']:>5.0%}"
        "   too short to contain review"
    )
    L.append(
        f"  working  <={p['break_ceiling_s']:>5.0f}s   "
        f"{result['working']['count_share']:>5.0%} / {result['working']['time_share']:>5.0%}"
        "   could be review -- or anything else"
    )
    L.append(
        f"  breaks   > {p['break_ceiling_s']:>5.0f}s   "
        f"{result['breaks']['count_share']:>5.0%} / {result['breaks']['time_share']:>5.0%}"
        "   the reviewer walked away"
    )
    L.append("")
    L.append(
        f"Upper bound on the dwell share of logged gap time: {bound:.2f}"
    )
    L.append(
        f"  (counting at most {p['max_review_s']:.0f}s of review per gap, none inside bursts)"
    )
    L.append("")
    L.append("Verdict:")
    if result["premise_holds"]:
        L.append(
            f"  The bound sits below {SWEEP_INFORMATIVE_DWELL:.2f}, the level at which the"
        )
        L.append(
            "  sensitivity sweep shows timestamps starting to carry engagement. Even on"
        )
        L.append(
            "  the most generous reading, this log's timestamps cannot say who reviewed"
        )
        L.append(
            "  and who rubber-stamped. The timing premise HOLDS here: the record is"
        )
        L.append("  blind, and only added instrumentation can change that.")
    else:
        L.append(
            f"  The bound sits at or above {SWEEP_INFORMATIVE_DWELL:.2f}, so this log's gaps"
        )
        L.append(
            "  COULD contain enough review time for timestamps to carry engagement."
        )
        L.append(
            "  That is not a finding that they do: the bound cannot convict, only"
        )
        L.append(
            "  exonerate, and gaps in the working range may be anything. To know,"
        )
        L.append(
            "  instrument dwell directly. Until then, do not lean on throughput as an"
        )
        L.append("  engagement signal, and do not assume the record is blind either.")
    return "\n".join(L)


def run_estimate(
    events: list[dict],
    burst_floor_s: float = 5.0,
    break_ceiling_s: float = 1800.0,
    max_review_s: float = 600.0,
) -> dict:
    result = estimate_log(
        events,
        burst_floor_s=burst_floor_s,
        break_ceiling_s=break_ceiling_s,
        max_review_s=max_review_s,
    )
    print(format_estimate(result))
    return result
