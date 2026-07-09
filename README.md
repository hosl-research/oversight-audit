# oversight-audit

**Does your AI-review logging record that a review happened, or whether it worked?**

Every AI-assisted review workflow produces a record: the item was triaged, the
output reviewed, the disposition approved and logged. Auditors check that record,
compliance trusts it, retrospectives lean on it. But a reviewer who examined an
AI-generated finding closely and a reviewer who cleared it without looking produce
the *same* record: a timestamp, an approval, a complete paper trail. The record
cannot place a reviewer anywhere on that spectrum.

`oversight-audit` does two honest things about that gap. It does **not** pretend to
recover engagement from a record that cannot carry it.

1. **`demo`** shows the gap on synthetic data with known ground truth: the fields a
   standard audit trail keeps separate engaged from procedural reviewers at close to
   chance, while function-level signals a standard trail does not keep separate them
   clearly.
2. **`check`** audits *your* review-log schema (the fields you actually capture) and
   reports which function-level signals you can and cannot compute from it. That is:
   what would change in your record if a reviewer stopped looking?

Zero dependencies. Python 3.9+. Clone and run.

---

## See the gap (about 30 seconds)

```
git clone https://github.com/<you>/oversight-audit.git
cd oversight-audit
python -m oversight_audit demo
```

```
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

Best a standard trail can do: 0.62. Best with function-level signals: 0.95.
```

The two populations did opposite things. On the record you keep, they are nearly
indistinguishable. The separation lives entirely in fields a standard audit trail
does not keep.

## Check your own logging

Describe the fields your review log captures in a small JSON file:

```json
{ "name": "our SOC review log", "fields": ["reviewer_id", "item_id", "decision", "decision_timestamp", "approver"] }
```

```
python -m oversight_audit check examples/typical_audit_schema.json
```

```
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
  Your record cannot distinguish substantive review from procedural review.
  Nothing in it would change if a reviewer stopped looking. Oversight is logged
  but unverifiable.
```

Point it at a schema listing your own fields (`examples/instrumented_schema.json`
shows what a capable log looks like). Field-name aliases are recognized, so
`timestamp`, `dwell_time`, `corrections`, and similar map onto the canonical names.

## What this does and does not claim

- It does **not** read your review data, and it does **not** detect rubber-stamping
  from a standard log. If the record cannot distinguish engaged from
  procedural review, no tool can extract that from it. Anything that claims to is
  selling you the thing this project says is impossible.
- It **does** show the distinction is real and invisible to a standard record, and
  it tells you whether your own logging is even capable of asking the question, plus
  the smallest thing you would have to instrument to change that.

The signals here are a starting agenda for oversight you can verify, not a finished
control set.

## The three function-level signals

Standard audit trails verify that a process was followed. These verify whether
judgment happened inside it. None require monitoring individuals; all can be built
into existing workflows.

- **Correction-rate trajectory.** Whether the rate of corrections is drifting down
  over time, an early sign scrutiny is thinning.
- **Validation load relative to output volume.** Whether reviewer capacity is being
  outpaced by how much the system produces.
- **Dependency accumulation.** Whether reliance on unmodified AI output is growing.

## "But I can just look at who is fast"

The one hint a standard trail seems to offer is throughput: the time between logged
decisions. The demo shows why it fails. That gap is dominated by queue wait,
context switching, and batching, not by how long anyone actually reviewed, so it
separates engaged from procedural reviewers only weakly (about 0.6 above), and it
collapses further under load, exactly when oversight matters most. A timestamp
records when a decision was logged, not how long review took.

## How the demo works

`generate` builds two populations of reviewers with a latent engagement level drawn
high for one group and low for the other, with deliberate overlap, because real
review falls on a spectrum. Both populations are tuned to the same decision
distribution, so approval looks identical. Every event carries ground-truth and
function-level fields alongside the standard ones. `signals` measures, for each
field, how well it separates the two groups (AUC via the Mann-Whitney statistic).
The contrast between the standard group and the function group is the point.

```
python -m oversight_audit generate --out mylog.json   # inspect the synthetic data
```

## Install

Runs from a clone with no install. To put it on your path:

```
pip install .
oversight-audit demo
```

## Contributing

Useful directions: additional function-level signals with their field requirements;
schema adapters for common review and ticketing systems; connectors that compute the
signals over a real instrumented log (on data that carries the function-level fields,
never a claim to recover them from a standard one). Open an issue or a pull request.

## Background

The framing comes from supervisory-control theory and human-factors research on
automation: oversight degrades under sustained load across security operations,
clinical decision support, and aviation, while the formal process stays intact.
High-capability models sharpen this, because fluent, confident output suppresses the
surface anomalies reviewers use to allocate attention. This repo is the practitioner
tool that follows from that argument.

Built by the [Human Oversight Systems Lab (HOSL)](https://github.com/hosl-research),
which studies how human oversight of AI degrades under load.

## License

MIT. See `LICENSE`.
