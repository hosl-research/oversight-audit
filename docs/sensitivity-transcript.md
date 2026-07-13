# `sensitivity` transcript

Live output at the default seed with 400 bootstrap resamples. The
baseline (0.00 on both axes) is the configuration `demo` runs.

```
$ python3 -m oversight_audit sensitivity --bootstrap 400

oversight-audit :: sensitivity of the non-identifiability result
==========================================================================
seed 20260709, 400 bootstrap resamples per level.
Baseline (level 0.00 on both axes) is the configuration the demo runs.

AXIS 1  DECISION DISAGREEMENT
  how far engaged and procedural reviewers diverge in logged decisions

  delta   standard sep [95% CI]        function sep [95% CI]
   0.00   0.62 [0.54,0.73] |##------|   0.95 [0.90,0.98] |#######-|
   0.15   0.67 [0.59,0.80] |###-----|   0.95 [0.91,0.99] |#######-|
   0.30   0.83 [0.74,0.90] |#####---|   0.96 [0.91,0.99] |#######-|
   0.45   0.88 [0.82,0.95] |######--|   0.96 [0.91,0.99] |#######-|
   0.60   0.92 [0.86,0.97] |#######-|   0.95 [0.90,0.99] |#######-|

  Standard separability moves 0.62 -> 0.92 as decisions diverge.
  In the agreement regime (0.00) the standard trail is near chance. It only
  sees engagement once the decisions themselves do, which is the regime where
  the failure is already visible without this tool.

AXIS 2  TIMESTAMP DWELL WEIGHT
  share of the logged inter-decision gap that is real review time

  weight   standard sep [95% CI]        function sep [95% CI]
   0.00   0.62 [0.55,0.73] |##------|   0.95 [0.90,0.99] |#######-|
   0.25   0.81 [0.71,0.91] |#####---|   0.95 [0.91,0.99] |#######-|
   0.50   0.91 [0.85,0.96] |#######-|   0.95 [0.91,0.98] |#######-|
   0.75   0.94 [0.88,0.98] |#######-|   0.95 [0.91,0.99] |#######-|
   1.00   0.94 [0.88,0.98] |#######-|   0.95 [0.91,0.99] |#######-|

  Standard separability moves 0.62 -> 0.94 as timestamps absorb dwell.
  At the baseline (0.00) timestamps are near chance. They carry engagement
  only when much of the logged gap is review time, which the workload
  literature says it is not.

--------------------------------------------------------------------------
Across both sweeps the function fields stay high while the standard fields
sit near chance until the failure is already in the decisions. The result is
not an artifact of the baseline configuration.
```
