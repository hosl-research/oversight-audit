# `estimate` transcript

Live output of the `estimate` command against the two example exports.
One log is exonerated; one cannot be. See README ("Test the timing
assumption on your own log") for how to read the bound.

## Batched queue export (premise holds)

```
$ python3 -m oversight_audit estimate examples/queue_export.json

oversight-audit :: could your timestamps carry engagement?
====================================================================
144 events, 4 reviewers, 140 inter-decision gaps (fields: reviewer_id, decision_timestamp).

Gap composition (share of gaps / share of gap time):
  bursts   <      5s     94% /    0%   too short to contain review
  working  <= 1800s      0% /    0%   could be review -- or anything else
  breaks   >  1800s      6% /  100%   the reviewer walked away

Upper bound on the dwell share of logged gap time: 0.05
  (counting at most 600s of review per gap, none inside bursts)

Verdict:
  The bound sits below 0.25, the level at which the
  sensitivity sweep shows timestamps starting to carry engagement. Even on
  the most generous reading, this log's timestamps cannot say who reviewed
  and who rubber-stamped. The timing premise HOLDS here: the record is
  blind, and only added instrumentation can change that.
```

## Session-structured export (no exoneration)

```
$ python3 -m oversight_audit estimate examples/deliberative_export.json

oversight-audit :: could your timestamps carry engagement?
====================================================================
60 events, 3 reviewers, 57 inter-decision gaps (fields: approver, decided_at).

Gap composition (share of gaps / share of gap time):
  bursts   <      5s      0% /    0%   too short to contain review
  working  <= 1800s    100% /  100%   could be review -- or anything else
  breaks   >  1800s      0% /    0%   the reviewer walked away

Upper bound on the dwell share of logged gap time: 0.90
  (counting at most 600s of review per gap, none inside bursts)

Verdict:
  The bound sits at or above 0.25, so this log's gaps
  COULD contain enough review time for timestamps to carry engagement.
  That is not a finding that they do: the bound cannot convict, only
  exonerate, and gaps in the working range may be anything. To know,
  instrument dwell directly. Until then, do not lean on throughput as an
  engagement signal, and do not assume the record is blind either.
```
