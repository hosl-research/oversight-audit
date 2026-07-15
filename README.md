# oversight-audit

**Does your AI-review logging record that a review happened, or whether it worked?**

[![oversight-audit demo: on a standard audit trail, engaged and procedural reviewers separate only weakly (0.62, where 0.50 is chance); on function-level signals they separate cleanly (0.95)](docs/demo.gif)](docs/demo-transcript.md)

*Same decisions. Same paper trail. Opposite behavior. The fields a standard audit
trail keeps (top) separate careful reviewers from rubber-stampers barely better
than chance. The fields it does not keep (bottom) separate them cleanly.*

Every AI-assisted review workflow produces a record: the item was triaged, the
output reviewed, the disposition approved and logged. Auditors check that record,
compliance trusts it, retrospectives lean on it. But a reviewer who examined an
AI-generated finding closely and a reviewer who cleared it without looking produce
the *same* record: a timestamp, an approval, a complete paper trail. The record
cannot place a reviewer anywhere on that spectrum.

`oversight-audit` does three honest things about that gap. It does **not** pretend
to recover engagement from a record that cannot carry it.

1. **`demo`** shows the gap on synthetic data with known ground truth: the fields a
   standard audit trail keeps separate engaged from procedural reviewers only weakly
   (0.62, where 0.50 is chance), while function-level signals a standard trail does
   not keep separate them clearly (0.95).
2. **`check`** audits *your* review-log schema (the fields you actually capture) and
   reports which function-level signals you can and cannot compute from it. That is:
   what would change in your record if a reviewer stopped looking?
3. **`estimate`** reads a real timestamped log and bounds how much engagement your
   timestamps *could* carry, so the argument's one contestable assumption gets
   tested on your own trail instead of taken on faith.

Zero dependencies. Python 3.9+. Clone and run.

---

## See the gap (about 30 seconds)

```
git clone https://github.com/<you>/oversight-audit.git
cd oversight-audit
python3 -m oversight_audit demo
```

```
oversight-audit :: can your record tell careful review from rubber-stamping?
============================================================================
80 reviewers (40 engaged, 40 procedural). Same task. Same decision mix.
Ground truth is known here. In a real audit it never is.

Score: how well each field separates engaged from procedural reviewers.
  0.50 = chance (the field tells you nothing)      1.00 = perfect

WHAT A STANDARD AUDIT TRAIL KEEPS  (decision, approval, timestamps)
  0.62  |######------------------|  time between logged decisions (throughput)
  0.53  |##----------------------|  approval rate
  0.51  |#-----------------------|  revise rate

WHAT IT DOES NOT KEEP  (requires added instrumentation)
  0.95  |######################--|  correction specificity
  0.94  |#####################---|  dwell time on the item
  0.92  |####################----|  evidence opened per item
  0.83  |################--------|  seeded-error catch rate
  0.82  |################--------|  accepted-unmodified rate

----------------------------------------------------------------------------
Best your audit trail can do: 0.62.    Best with the fields it drops: 0.95.

Two populations that did opposite things. Nearly identical on the record you keep.
Your record certifies that review happened, not that it worked.
```

The two populations did opposite things. On the record you keep, they are nearly
indistinguishable. The separation lives entirely in fields a standard audit trail
does not keep.

Note the throughput line. Timestamps are the one hint a standard trail seems to
offer, and it separates at 0.62, barely above chance, because the gap between two
logged decisions is dominated by queue wait, context switching, and batching, not
by how long anyone actually reviewed. The residue above 0.50 is deliberate: the
generator lets a faint trace of engagement bleed into the logged gaps, because
real trails are not perfectly silent either. The claim is not that a standard
trail carries *zero* signal. It is that the signal is too weak to act on, and it
stays that way unless a large share of the logged gap is real review time, which
is exactly what `sensitivity` quantifies and `estimate` bounds for your own log.

## See it one record at a time

The aggregate view proves the gap statistically. This shows it the way a person
feels it: six individual approvals as an audit trail records them, then the same
six with the ground truth the trail never had.

```
python3 -m oversight_audit reveal
```

```
AS THE AUDIT TRAIL RECORDS THEM
  #  reviewer   decision  approved  logged at
  1  rev-031    accept    yes       00:28:19
  2  rev-017    accept    yes       20:58:49
  ...

  Which three reviewers examined the item, and which three approved
  without looking? Guess, then read on.
..........................................................................
THE TRUTH THE RECORD COULD NOT SHOW
  #  reviewer   looked?         dwell   evidence  rationale
  1  rev-031    engaged          174s   opened    specific
  3  rev-075    rubber-stamped    38s   --        generic
  ...
```

Try it before you scroll: you cannot pick the three who looked. That failure is
the point. (These are clear cases chosen so the contrast reads; `demo` shows the
full population, where engagement is a spectrum.)

## Check your own logging

Describe the fields your review log captures in a small JSON file:

```json
{ "name": "our SOC review log", "fields": ["reviewer_id", "item_id", "decision", "decision_timestamp", "approver"] }
```

```
python3 -m oversight_audit check examples/typical_audit_schema.json
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
  [NO ] Are seeded known-answer items being caught?
        to compute: add item_is_golden

Computable: 0 of 5.

Verdict:
  Your record cannot distinguish substantive review from procedural review.
  Nothing in it would change if a reviewer stopped looking. Oversight is logged
  but unverifiable.
```

Point it at a schema listing your own fields (`examples/instrumented_schema.json`
shows what a capable log looks like). Field-name aliases are recognized, so
`timestamp`, `dwell_time`, `corrections`, and similar map onto the canonical names.
If `check` says your logging falls short and you want to fix it,
[docs/instrumented-log-format.md](docs/instrumented-log-format.md) specifies
exactly what to emit: field semantics, minimal vs. full profiles, and the
privacy line the signals are designed to respect.

`check` reads your schema, not your data, so it is a **necessary-condition test**.
A missing field proves a signal is uncomputable from your log. A present field only
makes it possible: a `dwell_time` column populated with garbage still passes.
Crossing the threshold means your logging is *capable of asking* whether review
functioned, not that it answers the question. The threshold is exactly one field
that records reviewer behavior rather than the decision (`evidence_opened`,
`time_on_item`, or `correction_specificity`). And one field
deserves a caveat: every schema has timestamps, and timestamps could in principle
carry review time. `check` counts them as standard-trail fields because in typical
queue systems the logged gap is dominated by everything except reviewing. If you
think your timestamps are different, `estimate` will bound how much they could
carry.

## Test the timing assumption on your own log

The argument's most contestable step is the premise that logged inter-decision
gaps contain almost no review time. `estimate` tests it against a real log: any
JSON list of events with a reviewer id and a decision timestamp:

```
python3 -m oversight_audit estimate mylog.json
```

It decomposes each reviewer's inter-decision gaps into bursts (too short to be
review, batched logging), breaks (too long, the reviewer walked away), and
working-range gaps, then reports an **upper bound** on the share of logged gap
time that could be review. Two honest asymmetries to keep in mind:

- The bound can **exonerate** timestamps but never convict them. A log whose gaps
  are dominated by bursts and breaks provably cannot carry much engagement. The
  premise holds and the non-identifiability argument applies with force. A log
  with a high bound only *might* carry engagement; whether reviewers actually
  spend the working gaps reviewing is unknowable without instrumenting dwell.
- Run it on `generate`'s own output and the bound comes back high even though the
  true dwell weight there is zero by construction. That is the bound working as
  designed, not failing.

Two example exports ship with the repo, one for each verdict:

```
python3 -m oversight_audit estimate examples/queue_export.json         # batched queue: premise holds
python3 -m oversight_audit estimate examples/deliberative_export.json  # session-structured: no exoneration
```

(Full output for both, and for `sensitivity`, is in
[docs/estimate-transcript.md](docs/estimate-transcript.md) and
[docs/sensitivity-transcript.md](docs/sensitivity-transcript.md).)

## Is the demo tuned? (`sensitivity`)

A constructive proof at one configuration invites the objection that the
configuration was chosen to produce the result. `sensitivity` sweeps the two
parameters that objection would target, with bootstrap confidence intervals:

```
python3 -m oversight_audit sensitivity --bootstrap 400
```

- **Decision disagreement** (0 → 0.6): standard-trail separability rises 0.62 →
  0.92 as engaged and procedural decisions diverge. The trail only sees engagement
  once the decisions themselves show the failure, the regime where no tool is
  needed.
- **Timestamp dwell weight** (0 → 1): standard-trail separability rises 0.62 →
  0.94, and reaches 0.81 by a dwell weight of 0.25. This is the decisive
  number: if even a quarter of the logged gap were real review time, timestamps
  would start to carry engagement. The argument therefore rests on that share
  being near zero, an empirical premise `estimate` lets you test on your own
  log rather than accept on faith.

At the baseline (0.00 on both axes, the demo's configuration): standard 0.62
[95% CI 0.54–0.74], function 0.95 [0.90–0.99], seed 20260709, 400 resamples.

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

## The four function-level signals

Standard audit trails verify that a process was followed. These verify whether
judgment happened inside it. None require monitoring individuals; all can be built
into existing workflows.

- **Correction-rate trajectory.** Whether the rate of corrections is drifting down
  over time, an early sign scrutiny is thinning.
- **Validation load relative to output volume.** Whether reviewer capacity is being
  outpaced by how much the system produces.
- **Dependency accumulation.** Whether reliance on unmodified AI output is growing.
- **Golden-task catch rate.** Whether seeded known-answer items are being caught.
  Unlike the others, this instruments the item stream rather than the reviewer: mix
  items with a known correct disposition into the queue, mark them in the log, and
  the ordinary decision field becomes an engagement measure. It is also the
  cheapest to add (one boolean column) and the demo already shows it working
  (the seeded-error catch line, 0.83).

A warning that belongs next to the agenda: once these signals are monitored, they
become targets. Dwell can be inflated by leaving the item open. Evidence-opens can
be clicked without reading. Rationale specificity can be padded with generated
text. Any calibrated instrument built on these signals has to treat gaming
resistance as a design criterion from the start, preferring signals that are
costly to fake, and cross-checking signals against each other rather than trusting
any one. Golden tasks are the benchmark here: passing them requires doing the
review, so their main gaming vector is not faking the signal but spotting the
golden items and engaging only on those, which is why they must be
indistinguishable from ordinary work. A signal that is cheap to fake measures
compliance with the metric, which is the same failure this tool exists to name.

## "But I can just look at who is fast"

The one hint a standard trail seems to offer is throughput: the time between logged
decisions. The demo shows why it fails. That gap is dominated by queue wait,
context switching, and batching, not by how long anyone actually reviewed, so it
separates engaged from procedural reviewers only weakly (about 0.6 above), and it
collapses further under load, exactly when oversight matters most. A timestamp
records when a decision was logged, not how long review took. If you suspect your
own system's timestamps are better than that, don't argue. Run
`estimate` on your log and see what they could carry at most.

## How the demo works

`generate` builds two populations of reviewers with a latent engagement level drawn
high for one group and low for the other, with deliberate overlap, because real
review falls on a spectrum. Both populations are tuned to the same decision
distribution, so approval looks identical. Every event carries ground-truth and
function-level fields alongside the standard ones. `signals` measures, for each
field, how well it separates the two groups (AUC via the Mann-Whitney statistic).
The contrast between the standard group and the function group is the point.

```
python3 -m oversight_audit generate --out mylog.json   # inspect the synthetic data
```

## Install

Runs from a clone with no install. To put it on your path:

```
pip install .
oversight-audit demo
```

## Contributing

Useful directions: additional function-level signals with their field requirements;
schema adapters for common review and ticketing systems; emitters that produce the
[instrumented log format](docs/instrumented-log-format.md) from real review tools;
connectors that compute the signals over a real instrumented log (on data that
carries the function-level fields, never a claim to recover them from a standard
one). Open an issue or a pull request.

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
