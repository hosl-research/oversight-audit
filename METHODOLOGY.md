# Methodology: what oversight-audit claims, and what it does not

## The claim

Reviewer engagement is not identifiable from a standard audit trail.

Stated precisely: let E be a reviewer's engagement on an item, whether they examined the
AI output or cleared it without looking. A standard audit trail records, per item, the
decision D (accept, revise, reject), the time the decision was logged T, and the approver
identity A. Call these S = (D, T, A). Engagement also expresses in behavior the trail does
not record: time on the item, whether evidence was opened, how specific a correction was.
Call these F.

The claim is about identifiability. In the regime described below, E cannot be recovered
from S by any method, because reviewers with opposite E produce the same distribution over
S. E can be recovered from F. A record that keeps only S certifies that a review occurred.
It cannot certify that the review functioned. No analysis of S will change that.

## The regime that matters

A standard trail records the decision D. If disengaged reviewers reached visibly worse
decisions than engaged ones, D would carry engagement, and this tool would be unnecessary:
the failure would read straight off the decisions.

The failure this tool addresses is the opposite case: the reviewer who approves the same
items a careful reviewer would have approved, without doing the reviewing. There the
decision distribution is equal across engagement levels, D and E are independent, and that
independence is not a convenience. It is the failure itself. Procedural review that reaches
correct-looking decisions is invisible because it agrees.

So the claim is scoped. Engagement is non-identifiable from the trail in the
decision-agreement regime, where procedural and engaged review reach the same decisions.
Outside that regime the trail sees the failure without help. Where the decisions already
show the problem, the tool adds nothing.

### Why engagement matters when the decisions agree

The scoping invites an objection worth answering head-on: if the disengaged reviewer
reaches the same decisions as the engaged one, what harm did disengagement do? The answer
is that oversight is not purchased for the items where it makes no difference. It is
purchased for the rare item where an engaged reviewer would have caught what a procedural
one waves through — the tail. On base rates the two reviewers agree, which is exactly why
agreement statistics cannot certify anything: they measure the items where engagement was
not needed. What the organization is paying for is the counterfactual catch rate on the
items where it is needed, and a reviewer who has stopped looking has the same expected
decision log and none of the tail coverage. Procedural review is insurance that stopped
paying claims while the premiums still clear. That is also why the failure compounds
silently: every quarter of clean agreement is consistent both with oversight that works
and with oversight that has quietly become a signature.

## Why S carries no engagement in that regime

S = (D, T, A).

- D is equal across engagement by the regime definition, so it carries nothing about E.
- A is the approver's identity, constant with respect to whether that approver engaged on a
  given item.
- T is the only field that could plausibly carry engagement. A timestamp would reflect it
  if the interval between logged decisions tracked how long review took. It does not, or
  only weakly. The interval is dominated by queue wait, context switching, and batching, not
  by reviewing time (see the timing note below). What remains after those factors is a faint
  and noisy trace of dwell, which is why timestamps separate engaged from procedural
  reviewers only slightly above chance, and separate them less under load.

So in the regime of concern, S says nothing about E. This follows from what the three
fields are: a decision held equal by the failure mode, an identity, and a timestamp
dominated by workflow. The audit trail produces the non-identifiability. A generator only
reproduces it.

## What makes engagement identifiable

F carries E because it records the reviewing behavior itself: dwell on the item, whether
supporting evidence was opened, the specificity of corrections, whether a seeded error was
caught. A log that records any of these crosses the identifiability threshold. It can ask
whether review functioned, beyond whether it happened. The `check` command reports whether a
given schema crosses that threshold and, if not, the smallest field that would.

## What the demo shows, and what it does not

The `demo` command constructs the non-identifiability rather than measuring it in the field.
It builds two reviewer populations with opposite engagement, tuned to the same decision
distribution (the regime above), and measures how well each field separates them. Standard
fields separate weakly. Function fields separate cleanly. This shows the pattern can
exist and holds together internally. It does not measure the size of the effect in any real
review system. It is not evidence that a given deployment sits in the failure regime. The
field magnitude is an empirical question this tool does not answer.

One number in the demo deserves explicit treatment, because a careful reader will notice
it: the best standard-trail field separates at 0.62, and 0.62 is not 0.50. The demo does
not claim the standard trail carries zero signal, and the generator does not produce a
trail that carries zero signal. It deliberately lets a faint trace of engagement bleed
into the logged inter-decision gaps (engaged reviewers average a few seconds longer
between logged decisions), because a synthetic trail that leaked nothing would be a
strawman — real trails are noisy, not silent. The claim is that the leak is too weak to
act on: at 0.62, ranking reviewers by throughput misclassifies too often to support any
intervention, and the residue shrinks further under load. The precise claim is therefore
"non-identifiable in practice from S in the agreement regime," where the demo's 0.62
[95% CI 0.54–0.74, seed 20260709, 400 bootstrap resamples] against the function fields'
0.95 [0.90–0.99] is the constructive exhibit. Anyone who wants to argue the 0.12 above
chance is actionable is welcome to; the sensitivity sweep shows what it would take for
that to become true, and `estimate` shows how to check whether it is true of a given log.

The sensitivity view addresses what a constructive proof cannot: whether the result depends
on the parameter values chosen. It sweeps two axes, the degree to which the two populations'
decisions disagree (moving out of the agreement regime) and the degree to which the
timestamp carries real dwell, and reports the separability of standard and function fields
across the space with bootstrap confidence intervals. The result to look for is this: across
the whole agreement regime the standard fields stay near chance while the function fields
track true engagement, and the point where the standard trail becomes informative is the
point where the failure is already visible in the decisions. The sweep does not estimate a
magnitude. It tests whether the qualitative result holds as the parameters change. If it
holds across the range, the result is not an artifact of one configuration.

## The timing assumption

The most contestable step is the claim that logged-decision timestamps carry little
engagement. It depends on a model of where inter-decision time goes. The human-factors and
supervisory-control work on workload and queueing supports treating that interval as
exogenously dominated, but it is an assumption, not a result. The sensitivity view
quantifies it: it lets the timestamp carry progressively more real dwell and reports how
much of the interval would have to be review time before the standard trail becomes
identifiable. If that threshold is high enough to be implausible, the assumption holds. The
reader can weigh that number instead of taking the assumption on faith.

The number is not comfortable, and it should be stated rather than softened: in the sweep,
standard-trail separability reaches 0.81 at a dwell weight of just 0.25 (seed 20260709).
If a quarter of the logged gap were real review time, timestamps would begin to carry
engagement. The assumption is therefore strong — near-zero dwell share — and whether it
holds is a property of the review system, not of the argument.

Where is it plausible? The assumption fits high-volume queue work, where decisions are
batched, items wait in queues, and reviewers context-switch: SOC alert triage, content
moderation, AI-output review embedded in ticketing systems, code review done in gaps
between other work. There, the logged gap is mostly everything except reviewing. The
assumption fits poorly where review is deliberative, single-case, and session-structured —
clinical chart review, IRB and grant review, judicial and parole decisions — where a
reviewer opens one case, works it, and logs it, so the gap approximates dwell. For systems
of that second kind the standard trail may genuinely carry engagement, the
non-identifiability claim weakens, and this tool's argument should not be recruited to
say otherwise. These domain names are priors about typical implementations, not verdicts:
a particular hospital's review workflow may be batch-logged and a particular SOC may be
session-structured, and what decides the question for any one system is the composition
of its logged gaps, not its industry. Readers should place their own system on that
spectrum, and the `estimate` command exists to adjudicate it: it decomposes a real log's inter-decision gaps into bursts,
breaks, and working-range time and reports an upper bound on the dwell share. The bound
is asymmetric by design — burst- and break-dominated gaps can prove the assumption holds,
but a high bound cannot prove it fails, since only instrumented dwell can show whether
working-range gaps contain reviewing.

## The four function-level signals and where they come from

The signals are not new constructs. They operationalize failure modes named in the
human-automation literature, chosen because each can be computed from fields a review log can
carry without monitoring individuals.

- Correction-rate trajectory: whether the rate of corrections drifts down over time. This
  tracks the erosion of active engagement Bainbridge described as the irony of automation,
  where the human kept for oversight is the one least practiced at exercising it, and the
  complacency effect Parasuraman and Manzey documented, where sustained reliable automation
  draws down monitoring.

- Validation load relative to output volume: whether reviewer capacity is outpaced by how
  much the system produces. This is the vigilance and workload problem in supervisory control
  (Parasuraman and Riley on when automation is used, misused, and disused), measurable as a
  ratio the log can report.

- Dependency accumulation: whether reliance on unmodified AI output is growing. This is
  overreliance and automation bias (Skitka and colleagues on automation bias in decision
  making; Lee and See on calibrated versus miscalibrated reliance; Schemmer and colleagues on
  appropriate reliance on AI advice), measured as the share of output accepted without
  modification.

- Golden-task catch rate: whether seeded known-answer items are being caught. Known-answer
  probing is the established practice wherever engagement must be measured without trusting
  self-report: attention checks in survey and experimental work (Oppenheimer and colleagues
  on instructional manipulation checks), gold-standard items in crowdsourced annotation
  (Snow and colleagues), and blind proficiency testing in laboratory quality assurance. It
  differs from the other three in kind: it instruments the item stream, not the reviewer,
  so it needs no behavioral capture at all -- only a marker for which items were golden,
  read against the decision field every trail already keeps. It is correspondingly the
  costliest signal to fake, since passing it requires performing the review; its own
  failure mode is distinguishability, reviewers learning to spot the golden items and
  engaging only on those. The demo's seeded-error catch line is this signal under its
  synthetic name.

These are a starting agenda for verifiable oversight. They are not a finished control set.

## When the signals become targets

The signals are safe to name because this tool only names them. The moment a later
instrument monitors them, Goodhart's law applies: a measure that becomes a target stops
being a good measure, and each of the three is fakeable at a known price. Dwell inflates
by leaving the item open. Evidence-opens inflate by clicking without reading. Rationale
specificity inflates by padding text, and cheaply now, since the reviewer being monitored
has access to the same class of model that produced the item under review. This is not a
reason to abandon the signals; decisions themselves are equally fakeable and we do not
abandon decisions. It is a design constraint on the calibrated instrument this project
points toward: prefer signals whose faking cost is high relative to the engagement they
proxy (a golden task passed is expensive to counterfeit; a click is not), read signals
jointly rather than singly, since faking all of them consistently approaches the cost of
just doing the review, and treat drift in the signals after instrumentation is announced
as itself diagnostic. Golden tasks anchor the costly end of that spectrum, with the caveat
that their gaming vector is detection rather than fabrication: they measure engagement
only while they are indistinguishable from ordinary work. An oversight lab should expect its own
instrument to induce the behavior it measures; designing for that is part of the
methodology, not a footnote to it.

## Limits

- The tool reasons about identifiability, not about any system's state. It tells you what
  your record could reveal. It says nothing about what your reviewers did.
- The demo is synthetic by necessity: it needs ground-truth engagement, which no real log
  carries. That is the same reason the field magnitude is out of reach.
- The signals require instrumentation the standard trail lacks. The tool exists to make the
  case for adding that instrumentation and to say what to add.

## References

- Bainbridge, L. (1983). Ironies of automation. *Automatica*, 19(6).
- Parasuraman, R., & Riley, V. (1997). Humans and automation: Use, misuse, disuse, abuse.
  *Human Factors*, 39(2).
- Skitka, L. J., Mosier, K. L., & Burdick, M. (1999). Does automation bias decision-making?
  *International Journal of Human-Computer Studies*, 51(5).
- Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance.
  *Human Factors*, 46(1).
- Parasuraman, R., & Manzey, D. H. (2010). Complacency and bias in human use of automation.
  *Human Factors*, 52(3).
- Schemmer, M., Kuehl, N., Benz, C., Bartos, A., & Satzger, G. (2023). Appropriate reliance
  on AI advice. *IUI 2023*.
- Snow, R., O'Connor, B., Jurafsky, D., & Ng, A. Y. (2008). Cheap and fast — but is it good?
  Evaluating non-expert annotations for natural language tasks. *EMNLP 2008*.
- Oppenheimer, D. M., Meyvis, T., & Davidenko, N. (2009). Instructional manipulation checks:
  Detecting satisficing to increase statistical power. *Journal of Experimental Social
  Psychology*, 45(4).
