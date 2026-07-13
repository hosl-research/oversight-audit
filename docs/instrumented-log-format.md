# The instrumented review log format (v0.2)

This is the log format the rest of this project's roadmap runs on. `check` tells
you whether your logging is capable of function-level oversight signals; this
document tells you exactly what to emit so that it is. A system that logs these
fields today will be readable by the v0.2 signal computation when it lands, and
by anything downstream of it. Emitting the format does not require adopting the
tool: the fields are useful to your own analysts regardless.

## Shape

A log is a JSON array (or JSON-lines stream) of event objects, one per review
decision. Field names below are canonical; `check` also recognizes the aliases
listed in its documentation (`timestamp`, `dwell_time`, `corrections`, `canary`,
and similar).

Include a `format_version` field on each event or at the top of the file:
`"oversight-audit-log/0.2"`.

## Standard fields (every trail has these already)

| field | type | semantics |
|---|---|---|
| `reviewer_id` | string | Stable pseudonymous identifier. Pseudonymize before export; nothing here needs a name. |
| `item_id` | string | The item reviewed. |
| `decision` | string | Your disposition vocabulary (`accept` / `revise` / `reject` or equivalent). |
| `decision_timestamp` | ISO 8601 string or epoch seconds | When the decision was **logged**. Not when review happened — that is the whole point of this project. |
| `approver` | string | Identity of record for the approval, if distinct from `reviewer_id`. |

## Function-level fields (the instrumentation)

Minimal profile: any one of the first three. Full profile: all of them.

| field | type | semantics |
|---|---|---|
| `time_on_item_s` | float, seconds | Active attention on the item: foreground focus, summed across visits. Not wall-clock time between open and close, and never derived from inter-decision gaps. If you cannot measure focus, log open-to-close per visit and say so. |
| `evidence_opened` | integer | Count of evidence artifacts (source document, model rationale, diff, linked case) actually opened for this item. Define "artifact" once, in your own docs, and keep it fixed. |
| `rationale_text` | string | The reviewer's written rationale, verbatim. Specificity is **computed downstream**, not logged — do not ask reviewers to self-rate. If text cannot leave your boundary, log `correction_specificity` (float 0–1) computed inside it and document the method. |
| `correction_count` | integer | Discrete corrections applied to the AI output before disposition. Zero for unmodified accepts. |
| `accepted_unmodified` | boolean | The AI output was used with no edits. Derivable from `correction_count` but worth logging explicitly, since it feeds dependency accumulation directly. |
| `item_presented_timestamp` | ISO 8601 or epoch seconds | When the item was first shown to the reviewer. With `decision_timestamp` this bounds true latency; with `items_presented_count` it measures load. |
| `items_presented_count` | integer | Items in the reviewer's queue at presentation time (or per session). Feeds validation load vs. volume. |
| `item_is_golden` | boolean | This item was a seeded known-answer probe. The cheapest instrumentation in this table — one boolean — and the hardest signal to fake. Keep golden items indistinguishable from ordinary work, and keep the expected disposition out of the review-time log (join it back at analysis time by `item_id`). |

## What not to do with it

The same properties that make these fields good oversight signals make them
tempting for individual surveillance, which would be both an ethical failure and
a practical one: reviewers who are being individually scored on dwell will game
dwell, and the signal dies. The signals are designed to be read at the cohort
and system level — is scrutiny thinning, is load outpacing capacity, is
dependence growing — on pseudonymized identifiers, with golden-task results
handled as calibration data, not performance data. If your deployment cannot
hold that line, instrument the item stream only (`item_is_golden`) and leave
behavioral capture out.

## Relation to `check` and the roadmap

`check` run against a schema listing these fields reports all five signals
computable. The v0.2 milestone computes the signals over a log in this format;
the calibrated instrument after it adds thresholds and gaming-resistance
cross-checks (see METHODOLOGY, "When the signals become targets"). The format is
versioned so those steps can extend it without breaking emitters.
