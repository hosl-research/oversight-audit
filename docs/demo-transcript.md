# Demo transcript

Verbatim output of the three commands, on the bundled synthetic data and example
schemas. Nothing here is edited. Reproduce with a clone and `python3 -m oversight_audit ...`.

---

## 1. The identity demonstration

Two populations of reviewers, ground truth known. The question asked of every
field: how well does it separate an engaged reviewer from a procedural one?
0.50 is a coin flip, 1.00 is perfect.

```console
$ python3 -m oversight_audit demo
oversight-audit :: the identity demonstration
============================================================
80 reviewers (40 engaged, 40 procedural), known ground truth.

How well does each field separate engaged from procedural?
  0.50 = chance (the field carries no information)
  1.00 = perfect

In a standard audit trail (decision, approval, timestamps):
  0.62  |######------------------|  time between logged decisions (throughput)
  0.53  |##----------------------|  approval rate
  0.51  |#-----------------------|  revise rate

Requires added instrumentation (not in a standard trail):
  0.95  |######################--|  correction specificity
  0.94  |#####################---|  dwell time on the item
  0.92  |####################----|  evidence opened per item
  0.83  |################--------|  seeded-error catch rate
  0.82  |################--------|  accepted-unmodified rate

------------------------------------------------------------
Best a standard trail can do: 0.62. Best with function-level signals: 0.95.
```

The two populations did opposite things. On the record you keep, they are nearly
indistinguishable.

Note the throughput line. Timestamps are the one hint a standard trail seems to
offer, and it separates at 0.62, barely above chance, because the gap between two
logged decisions is dominated by queue wait, context switching, and batching, not
by how long anyone actually reviewed.

---

## 2. Instrumentation self-audit: a typical audit trail

The tool reads your schema, not your data. Here is what a conventional
review log can and cannot answer.

```console
$ python3 -m oversight_audit check examples/typical_audit_schema.json
oversight-audit :: instrumentation self-audit (typical AI-review audit trail)
============================================================
Recognized fields: approver, decision, decision_timestamp, item_id, reviewer_id

Function-level oversight signals:
  [NO ] Can a substantive review be told apart from a procedural one?
        to compute: add one of {evidence_opened, time_on_item, correction_specificity}
  [NO ] Is the correction rate drifting down over time?
        to compute: add correction_count
  [NO ] Is reviewer capacity being outpaced by output volume?
        to compute: add one of {items_presented_count, item_presented_timestamp}
  [NO ] Is reliance on unmodified AI output growing?
        to compute: add accepted_unmodified

Computable: 0 of 4.

Verdict:
  Your record cannot distinguish substantive review from
  procedural review. Nothing in it would change if a
  reviewer stopped looking. Oversight is logged but
  unverifiable.
```

Every NO comes with the smallest field that would turn it into a YES.

---

## 3. Instrumentation self-audit: a log built to answer the question

```console
$ python3 -m oversight_audit check examples/instrumented_schema.json
oversight-audit :: instrumentation self-audit (function-instrumented review log)
============================================================
Recognized fields: accepted_unmodified, correction_count, correction_specificity,
decision, decision_timestamp, evidence_opened, item_id, items_presented_count,
reviewer_id, time_on_item

Function-level oversight signals:
  [YES] Can a substantive review be told apart from a procedural one?
  [YES] Is the correction rate drifting down over time?
  [YES] Is reviewer capacity being outpaced by output volume?
  [YES] Is reliance on unmodified AI output growing?

Computable: 4 of 4.

Verdict:
  You can compute all function-level signals defined here.
  Your logging is capable of asking whether oversight is
  working, not just that it happened. These signals are a
  starting agenda, not a finished control set.
```

---

## 4. Inspect the synthetic data

Nothing is hidden. Dump the event log the demo runs on and read it.

```console
$ python3 -m oversight_audit generate --out mylog.json
wrote 3200 events to mylog.json
```

One event, showing the three layers: the standard-trail fields an auditor would
have, the ground truth an auditor would never have, and the function-level fields
that only exist if someone instrumented for them.

```json
{
  "reviewer_id": "rev-006",
  "item_id": "item-rev-006-000",
  "decision": "revise",
  "decision_timestamp": 1700000361.3,
  "approver": "rev-006",

  "engaged": true,
  "item_has_seeded_error": false,

  "evidence_opened": 1,
  "time_on_item_s": 99.6,
  "correction_count": 2,
  "correction_specificity": 0.5,
  "caught_seeded_error": false,
  "accepted_unmodified": false
}
```

Strip the middle block (ground truth) and the bottom block (function-level fields)
and you are left with what a standard audit trail keeps. That is the whole argument
in one record.
