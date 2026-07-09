"""
Synthetic review-log generator with known ground truth.

Two populations of reviewers process the same stream of AI-generated items:

  - engaged reviewers open the evidence, spend real time, write specific
    corrections, and catch the seeded errors at a higher rate;
  - procedural reviewers approve quickly, rarely open the evidence, write generic
    rationales, and catch seeded errors at close to the base rate of noticing
    nothing.

Both populations are tuned to the same decision distribution (about the same
approval rate), so the thing a standard audit trail keeps -- the decision and the
approval -- looks the same for both. The difference lives entirely in fields a
standard trail does not keep.

Every event carries:
  - a ground-truth `engaged` flag (never available to a real auditor);
  - standard-record fields (reviewer_id, item_id, decision, decision_timestamp,
    approver) that a typical audit trail keeps;
  - function-level fields (evidence_opened, time_on_item_s, correction_count,
    correction_specificity, caught_seeded_error, accepted_unmodified) that a
    standard trail does not keep unless someone instruments for them.

Pure standard library. Deterministic for a fixed seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict, field
from typing import Optional


DECISIONS = ("accept", "revise", "reject")


@dataclass
class ReviewEvent:
    # --- standard audit-trail fields (what a typical log keeps) ---
    reviewer_id: str
    item_id: str
    decision: str
    decision_timestamp: float          # unix-like seconds
    approver: str
    # --- ground truth (never available to a real auditor) ---
    engaged: bool
    item_has_seeded_error: bool
    # --- function-level fields (require added instrumentation) ---
    evidence_opened: int               # count of evidence panels opened
    time_on_item_s: float              # dwell time on the item itself
    correction_count: int
    correction_specificity: float      # 0..1, how specific the written rationale is
    caught_seeded_error: bool          # flagged the seeded error when present
    accepted_unmodified: bool          # accepted the AI output with no change

    def to_dict(self) -> dict:
        return asdict(self)


def _decision(rng: random.Random) -> str:
    # Same distribution for both populations: approval-heavy, as real queues are.
    r = rng.random()
    if r < 0.70:
        return "accept"
    if r < 0.90:
        return "revise"
    return "reject"


def generate_log(
    n_reviewers: int = 80,
    items_per_reviewer: int = 40,
    engaged_fraction: float = 0.5,
    seeded_error_rate: float = 0.30,
    seed: int = 20260709,
) -> list[dict]:
    """
    Return a list of review-event dicts across `n_reviewers` reviewers, half of
    them engaged (rounded), each processing `items_per_reviewer` items.
    """
    rng = random.Random(seed)
    n_engaged = round(n_reviewers * engaged_fraction)
    reviewers = [(f"rev-{i:03d}", i < n_engaged) for i in range(n_reviewers)]
    rng.shuffle(reviewers)

    events: list[dict] = []
    clock = 1_700_000_000.0  # arbitrary epoch base

    for reviewer_id, engaged in reviewers:
        # Engagement is a spectrum, not a switch: "most real review falls in
        # between." Each reviewer gets a latent engagement level, drawn high for
        # the engaged group and low for the procedural group, but the two
        # distributions overlap, so the populations are not cleanly separable even
        # on the function-level signals -- they are strongly, not perfectly, so.
        base = 0.72 if engaged else 0.30
        latent = min(1.0, max(0.0, rng.gauss(base, 0.16)))

        for j in range(items_per_reviewer):
            item_id = f"item-{reviewer_id}-{j:03d}"
            has_error = rng.random() < seeded_error_rate
            difficulty = rng.random()  # affects dwell for everyone

            decision = _decision(rng)
            approved = decision == "accept"

            # Function-level fields track the latent engagement level (with noise).
            evidence_opened = sum(1 for _ in range(2) if rng.random() < 0.10 + 0.75 * latent)
            time_on_item_s = max(2.0, rng.gauss(15 + 150 * latent + 30 * difficulty, 22))
            if decision == "accept":
                correction_count = 0
            else:
                correction_count = 1 + int(round(rng.random() * 3 * latent))
            correction_specificity = min(1.0, max(0.0, rng.gauss(0.20 + 0.60 * latent, 0.13)))
            caught = has_error and rng.random() < 0.18 + 0.68 * latent
            accepted_unmodified = approved and rng.random() < 0.88 - 0.55 * latent
            # The gap between two LOGGED decisions is not the time spent reviewing.
            # It is dominated by exogenous factors -- queue wait, context switching,
            # batching, breaks -- that are independent of engagement. A standard
            # trail's timestamps record when a decision was logged, not how long
            # review took, so throughput derived from them is only a weak,
            # confounded hint. (The real dwell, time_on_item_s, is a function-level
            # field you only have if you instrument for it.)
            exogenous_gap = rng.gauss(150, 120)
            engagement_bleed = rng.gauss(6 if engaged else 0, 10)
            clock += max(5.0, exogenous_gap + engagement_bleed)

            events.append(
                ReviewEvent(
                    reviewer_id=reviewer_id,
                    item_id=item_id,
                    decision=decision,
                    decision_timestamp=round(clock, 1),
                    approver=reviewer_id,
                    engaged=engaged,
                    item_has_seeded_error=has_error,
                    evidence_opened=evidence_opened,
                    time_on_item_s=round(time_on_item_s, 1),
                    correction_count=correction_count,
                    correction_specificity=round(correction_specificity, 3),
                    caught_seeded_error=caught,
                    accepted_unmodified=accepted_unmodified,
                ).to_dict()
            )
    return events
