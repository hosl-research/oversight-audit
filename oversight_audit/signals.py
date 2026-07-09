"""
Separability analysis: how well can a given field distinguish an engaged
reviewer from a procedural one?

We aggregate the event log to one row per reviewer, then for each field compute
the AUC of that field against the ground-truth `engaged` label. AUC 0.5 is chance
(the field carries no information about engagement); AUC 1.0 is perfect.

Fields are split into two groups:
  - STANDARD: derivable from what a typical audit trail keeps (decision, approval,
    and the timestamps between logged decisions);
  - FUNCTION: require added instrumentation (evidence opened, dwell time on the
    item, correction specificity, seeded-error catch rate, unmodified-accept rate).

The point of the demonstration is the contrast between the two groups' AUCs.
Pure standard library.
"""

from __future__ import annotations

from statistics import mean


def auc(pos: list[float], neg: list[float]) -> float:
    """Area under the ROC curve via the Mann-Whitney U statistic. O(n log n)."""
    if not pos or not neg:
        return 0.5
    labeled = [(v, 1) for v in pos] + [(v, 0) for v in neg]
    labeled.sort(key=lambda t: t[0])
    # assign average ranks, handling ties
    ranks = [0.0] * len(labeled)
    i = 0
    while i < len(labeled):
        j = i
        while j + 1 < len(labeled) and labeled[j + 1][0] == labeled[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # ranks are 1-based
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    rank_sum_pos = sum(r for r, (_, lab) in zip(ranks, labeled) if lab == 1)
    n_pos, n_neg = len(pos), len(neg)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def separability(pos: list[float], neg: list[float]) -> float:
    """Direction-free separability in [0.5, 1.0]: how far from chance the field is."""
    a = auc(pos, neg)
    return max(a, 1.0 - a)


def aggregate_by_reviewer(events: list[dict]) -> list[dict]:
    """Collapse the event log to one feature row per reviewer."""
    by_rev: dict[str, list[dict]] = {}
    for e in events:
        by_rev.setdefault(e["reviewer_id"], []).append(e)

    rows: list[dict] = []
    for rid, evs in by_rev.items():
        evs_sorted = sorted(evs, key=lambda e: e["decision_timestamp"])
        gaps = [
            b["decision_timestamp"] - a["decision_timestamp"]
            for a, b in zip(evs_sorted, evs_sorted[1:])
        ]
        seeded = [e for e in evs if e["item_has_seeded_error"]]
        rows.append(
            {
                "reviewer_id": rid,
                "engaged": bool(evs[0]["engaged"]),
                # --- STANDARD: from decision / approval / timestamps ---
                "approval_rate": mean(1.0 if e["decision"] == "accept" else 0.0 for e in evs),
                "revise_rate": mean(1.0 if e["decision"] == "revise" else 0.0 for e in evs),
                "mean_review_gap_s": mean(gaps) if gaps else 0.0,
                # --- FUNCTION: require added instrumentation ---
                "evidence_open_rate": mean(float(e["evidence_opened"]) for e in evs),
                "mean_time_on_item_s": mean(float(e["time_on_item_s"]) for e in evs),
                "mean_correction_specificity": mean(float(e["correction_specificity"]) for e in evs),
                "seeded_error_catch_rate": (
                    mean(1.0 if e["caught_seeded_error"] else 0.0 for e in seeded) if seeded else 0.0
                ),
                "unmodified_accept_rate": mean(1.0 if e["accepted_unmodified"] else 0.0 for e in evs),
            }
        )
    return rows


# field -> ("STANDARD"|"FUNCTION", human label)
FEATURES: dict[str, tuple[str, str]] = {
    "approval_rate": ("STANDARD", "approval rate"),
    "revise_rate": ("STANDARD", "revise rate"),
    "mean_review_gap_s": ("STANDARD", "time between logged decisions (throughput)"),
    "evidence_open_rate": ("FUNCTION", "evidence opened per item"),
    "mean_time_on_item_s": ("FUNCTION", "dwell time on the item"),
    "mean_correction_specificity": ("FUNCTION", "correction specificity"),
    "seeded_error_catch_rate": ("FUNCTION", "seeded-error catch rate"),
    "unmodified_accept_rate": ("FUNCTION", "accepted-unmodified rate"),
}


def separability_report(events: list[dict]) -> dict:
    """
    Per-field separability of engaged vs procedural reviewers, plus the best
    separability within each of the STANDARD and FUNCTION groups.
    """
    rows = aggregate_by_reviewer(events)
    pos = [r for r in rows if r["engaged"]]
    neg = [r for r in rows if not r["engaged"]]

    fields = []
    for name, (group, label) in FEATURES.items():
        s = separability([r[name] for r in pos], [r[name] for r in neg])
        fields.append({"field": name, "label": label, "group": group, "separability": round(s, 3)})

    best_standard = max((f["separability"] for f in fields if f["group"] == "STANDARD"), default=0.5)
    best_function = max((f["separability"] for f in fields if f["group"] == "FUNCTION"), default=0.5)
    return {
        "n_reviewers": len(rows),
        "n_engaged": len(pos),
        "n_procedural": len(neg),
        "fields": sorted(fields, key=lambda f: (f["group"], -f["separability"])),
        "best_standard": round(best_standard, 3),
        "best_function": round(best_function, 3),
    }
