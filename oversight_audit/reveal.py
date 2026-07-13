"""
The record-level reveal.

The aggregate demo (demo.py) proves the gap statistically. This shows it at the
level a person feels: six individual review records, printed first exactly as an
audit trail keeps them, and then again with the ground truth the trail never had.

The records are chosen so their visible fields look alike (all approvals), so a
viewer cannot pick the engaged reviewers from the procedural ones. The reveal
shows that behind six identical-looking approvals, three reviewers examined the
item and three did not, and that not one column an ordinary audit trail keeps
would have told you which was which.

Domain-neutral on purpose: "reviewer", "item", "approval" apply to any
AI-assisted review workflow, not just security operations.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone

from .generate import generate_log


def _clock(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")


def select_records(seed: int = 20260709, n_each: int = 3) -> list[dict]:
    """
    Pick n_each clearly-engaged and n_each clearly-procedural reviewers, one
    representative approval each, then shuffle so the display order does not leak
    the answer.

    These are clear cases chosen so the contrast is legible; engagement is a
    spectrum with overlap (see demo.py), and this view sits at its two ends on
    purpose. The aggregate demo is where the honest, overlapping population lives.
    """
    events = generate_log(seed=seed)
    by_rev: dict[str, list[dict]] = {}
    for e in events:
        by_rev.setdefault(e["reviewer_id"], []).append(e)

    def mean_dwell(rid: str) -> float:
        evs = by_rev[rid]
        return sum(x["time_on_item_s"] for x in evs) / len(evs)

    engaged_revs = sorted(
        (r for r, evs in by_rev.items() if evs[0]["engaged"]),
        key=lambda r: -mean_dwell(r),
    )[:n_each]
    procedural_revs = sorted(
        (r for r, evs in by_rev.items() if not evs[0]["engaged"]),
        key=mean_dwell,
    )[:n_each]

    chosen: list[dict] = []
    for rid in engaged_revs + procedural_revs:
        accepts = [e for e in by_rev[rid] if e["decision"] == "accept"] or by_rev[rid]
        m = mean_dwell(rid)
        chosen.append(min(accepts, key=lambda e: abs(e["time_on_item_s"] - m)))
    random.Random(seed).shuffle(chosen)
    return chosen


def format_reveal(records: list[dict]) -> str:
    L = []
    L.append("oversight-audit :: six approvals. which reviewers actually looked?")
    L.append("=" * 74)
    L.append("")
    L.append("AS THE AUDIT TRAIL RECORDS THEM")
    L.append("  #  reviewer   decision  approved  logged at")
    for i, r in enumerate(records, 1):
        L.append(f"  {i}  {r['reviewer_id']:<9}  {r['decision']:<8}  yes       {_clock(r['decision_timestamp'])}")
    L.append("")
    L.append("Six complete records. Six logged approvals. Which three reviewers")
    L.append("examined the item, and which three approved without looking? Guess,")
    L.append("then read on.")
    L.append("")
    L.append("." * 74)
    L.append("")
    L.append("THE TRUTH THE RECORD COULD NOT SHOW")
    L.append("  #  reviewer   looked?         dwell   evidence  rationale")
    for i, r in enumerate(records, 1):
        looked = "engaged" if r["engaged"] else "rubber-stamped"
        dwell = f"{int(round(r['time_on_item_s']))}s"
        ev = "opened" if r["evidence_opened"] else "--"
        spec = "specific" if r["correction_specificity"] >= 0.5 else "generic"
        L.append(f"  {i}  {r['reviewer_id']:<9}  {looked:<14}  {dwell:>5}   {ev:<8}  {spec}")
    L.append("")
    L.append("Same six records. Same six approvals. Three looked, three did not.")
    L.append("The audit trail kept none of the columns that tell them apart.")
    L.append("")
    L.append("(Clear cases, chosen so the contrast reads. Engagement is a spectrum;")
    L.append("run `oversight-audit demo` for the full, overlapping population.)")
    return "\n".join(L)


def run_reveal(seed: int = 20260709) -> list[dict]:
    records = select_records(seed=seed)
    print(format_reveal(records))
    return records
