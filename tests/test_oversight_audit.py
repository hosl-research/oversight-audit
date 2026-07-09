"""Tests for oversight-audit. Pure standard library; run with pytest or unittest."""

from __future__ import annotations

from oversight_audit.generate import generate_log
from oversight_audit.signals import auc, separability, separability_report
from oversight_audit.schema_audit import audit_schema


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
    # The demonstration's whole claim: standard-trail fields are near chance,
    # function-level signals separate clearly.
    report = separability_report(generate_log(seed=20260709))
    assert report["best_standard"] < 0.70, report["best_standard"]
    assert report["best_function"] > 0.80, report["best_function"]
    assert report["best_function"] - report["best_standard"] > 0.15


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


def test_schema_audit_accepts_aliases():
    # aliases should normalize onto canonical field names
    result = audit_schema(["reviewer_id", "decided_at", "dwell_time"])
    subst = next(s for s in result["signals"] if s["signal"] == "substantive_vs_procedural")
    assert subst["computable"] is True  # dwell_time -> time_on_item satisfies it
