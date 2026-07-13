"""Tests for oversight-audit. Pure standard library; run with pytest or unittest."""

from __future__ import annotations

from oversight_audit.generate import generate_log
from oversight_audit.signals import auc, separability, separability_report
from oversight_audit.schema_audit import audit_schema
from oversight_audit.reveal import select_records
from oversight_audit.sensitivity import run_sensitivity
from oversight_audit.estimate import estimate_log


def test_auc_basic():
    assert auc([3, 4, 5], [0, 1, 2]) == 1.0
    assert auc([0, 1, 2], [3, 4, 5]) == 0.0
    assert abs(auc([1, 2, 3], [1, 2, 3]) - 0.5) < 1e-9
    assert separability([0, 1, 2], [3, 4, 5]) == 1.0  # direction-free


def test_generator_is_deterministic():
    a = generate_log(seed=1)
    b = generate_log(seed=1)
    assert a == b
    assert generate_log(seed=2) != a


def test_generator_shape_and_ground_truth():
    events = generate_log(n_reviewers=10, items_per_reviewer=5, seed=7)
    assert len(events) == 50
    reviewers = {e["reviewer_id"] for e in events}
    assert len(reviewers) == 10
    # roughly balanced ground truth
    engaged = {e["reviewer_id"] for e in events if e["engaged"]}
    assert 3 <= len(engaged) <= 7


def test_the_identity_contrast_holds():
    # The demonstration's whole claim: standard-trail fields separate weakly,
    # function-level signals separate clearly.
    report = separability_report(generate_log(seed=20260709))
    assert report["best_standard"] < 0.70, report["best_standard"]
    assert report["best_function"] > 0.80, report["best_function"]
    assert report["best_function"] - report["best_standard"] > 0.15


def test_headline_numbers_are_pinned():
    # The README, METHODOLOGY, the OASec materials, and the demo GIF all cite
    # 0.62 / 0.95 at the default seed. If a generator change moves these, every
    # published claim moves with it -- this must be a deliberate act, not drift.
    report = separability_report(generate_log(seed=20260709))
    assert report["best_standard"] == 0.619, report["best_standard"]
    assert report["best_function"] == 0.954, report["best_function"]


def test_schema_audit_typical_is_blind():
    result = audit_schema(["reviewer_id", "item_id", "decision", "decision_timestamp", "approver"])
    assert result["computable_count"] == 0
    assert "unverifiable" in result["verdict"]


def test_schema_audit_instrumented_is_capable():
    result = audit_schema(
        ["reviewer_id", "item_id", "decision", "decision_timestamp",
         "evidence_opened", "time_on_item", "correction_count",
         "correction_specificity", "accepted_unmodified", "items_presented_count"]
    )
    assert result["computable_count"] == result["total_signals"]


def test_reveal_records_are_balanced_and_clear():
    recs = select_records()
    assert len(recs) == 6
    assert sum(1 for r in recs if r["engaged"]) == 3
    assert all(r["decision"] == "accept" for r in recs)          # uniform visible record
    assert len({r["reviewer_id"] for r in recs}) == 6            # no reviewer twice
    # clear archetypes: engaged dwell clearly separated from procedural
    eng = [r["time_on_item_s"] for r in recs if r["engaged"]]
    proc = [r["time_on_item_s"] for r in recs if not r["engaged"]]
    assert min(eng) > max(proc)


def test_schema_audit_accepts_aliases():
    # aliases should normalize onto canonical field names
    result = audit_schema(["reviewer_id", "decided_at", "dwell_time"])
    subst = next(s for s in result["signals"] if s["signal"] == "substantive_vs_procedural")
    assert subst["computable"] is True  # dwell_time -> time_on_item satisfies it


def test_default_generator_unchanged_by_new_params():
    # The sensitivity parameters default to a no-op: same log as before.
    a = generate_log(seed=123)
    b = generate_log(seed=123, decision_disagreement=0.0, timestamp_dwell_weight=0.0)
    assert a == b


def test_decision_disagreement_makes_the_standard_trail_see():
    # In the agreement regime the standard trail is near chance; as decisions
    # diverge, the decision itself starts to carry engagement.
    base = separability_report(generate_log(seed=20260709, decision_disagreement=0.0))
    high = separability_report(generate_log(seed=20260709, decision_disagreement=0.60))
    assert base["best_standard"] < 0.70
    assert high["best_standard"] > base["best_standard"] + 0.05


def test_timestamp_dwell_makes_throughput_informative():
    # Blending real dwell into the logged gap makes timestamps informative.
    base = separability_report(generate_log(seed=20260709, timestamp_dwell_weight=0.0))
    high = separability_report(generate_log(seed=20260709, timestamp_dwell_weight=1.0))
    assert high["best_standard"] > base["best_standard"] + 0.10


def _events(rows):
    return [{"reviewer_id": r, "decision_timestamp": t} for r, t in rows]


def test_estimate_burst_dominated_log_exonerates_timestamps():
    # Decisions logged in machine-speed bursts: gaps cannot contain review.
    rows = [("rev-a", 1000.0 + i * 0.5) for i in range(50)]
    rows += [("rev-b", 2000.0 + i * 0.5) for i in range(50)]
    result = estimate_log(_events(rows))
    assert result["bursts"]["count_share"] == 1.0
    assert result["dwell_share_upper_bound"] == 0.0
    assert result["premise_holds"] is True


def test_estimate_break_dominated_log_exonerates_timestamps():
    # A handful of decisions hours apart: at most max_review of each gap is dwell.
    rows = [("rev-a", 1000.0 + i * 7200.0) for i in range(10)]
    result = estimate_log(_events(rows))
    assert result["breaks"]["count_share"] == 1.0
    # 600s of a 7200s gap
    assert abs(result["dwell_share_upper_bound"] - 600.0 / 7200.0) < 0.01
    assert result["premise_holds"] is True


def test_estimate_working_range_log_cannot_be_exonerated():
    # Gaps that sit squarely in the plausible-review range: the bound is high,
    # which convicts nothing but refuses to exonerate.
    rows = [("rev-a", 1000.0 + i * 120.0) for i in range(30)]
    result = estimate_log(_events(rows))
    assert result["working"]["count_share"] == 1.0
    assert result["dwell_share_upper_bound"] == 1.0
    assert result["premise_holds"] is False


def test_estimate_on_synthetic_log_returns_high_bound_by_design():
    # The generator's baseline has TRUE dwell weight zero, but its gaps sit in
    # the working range, so the upper bound is high. The bound can only
    # exonerate timestamps, never convict them -- this asymmetry is documented.
    result = estimate_log(generate_log(seed=20260709))
    assert result["premise_holds"] is False


def test_estimate_accepts_aliases_and_iso_timestamps():
    events = [
        {"approver": "a", "decided_at": "2026-07-01T09:00:00"},
        {"approver": "a", "decided_at": "2026-07-01T09:00:02"},
        {"approver": "a", "decided_at": "2026-07-01T09:00:04"},
    ]
    result = estimate_log(events)
    assert result["reviewer_field"] == "approver"
    assert result["timestamp_field"] == "decided_at"
    assert result["bursts"]["count"] == 2


def test_estimate_rejects_unusable_logs():
    try:
        estimate_log([])
    except ValueError:
        pass
    else:
        raise AssertionError("empty log should raise")
    try:
        estimate_log([{"reviewer_id": "a", "decision_timestamp": 1.0}])
    except ValueError:
        pass
    else:
        raise AssertionError("single-event-per-reviewer log should raise")


def test_sensitivity_report_structure_and_direction():
    res = run_sensitivity(seed=20260709, bootstrap=60)
    assert set(res) >= {"decision_disagreement", "timestamp_dwell_weight"}

    dis = res["decision_disagreement"]
    assert dis[0]["level"] == 0.0
    # baseline: standard near chance, function clearly separating
    assert dis[0]["standard"]["sep"] < 0.70
    assert dis[0]["function"]["sep"] > 0.80
    # CI is well-formed and in range
    s0 = dis[0]["standard"]
    assert 0.5 <= s0["lo"] <= s0["hi"] <= 1.0
    # standard separability rises across the disagreement axis
    assert dis[-1]["standard"]["sep"] > dis[0]["standard"]["sep"]

    dw = res["timestamp_dwell_weight"]
    assert dw[0]["level"] == 0.0
    assert dw[-1]["standard"]["sep"] > dw[0]["standard"]["sep"]
