# Bounded allocation-quality proposal

Ticket: `ticket-c9ce79e3c539ee44`  
Consumer: `bounded_owner_allocation_experiment_proposal`  
Probe seed: `ed204f09b0359ea28175e9017cfa12740e7d7c7ec1a265c4d089a618b913dc86`

## Observed sample

The ticket sampler selected `9af68e46cf69`, `46c02325ed3b`, and
`01f4294de005` from 300 packet records. The one bounded probe generated seven
lawful, distinct inputs for each record with zero duplicate, grammar, or
exception rejections. Each exact canonical program then labelled all seven
inputs through the protected Racket runtime. Measured Racket wall times were
2.502325 s, 2.389777 s, and 2.169169 s respectively. These timings measure only
this small execution smoke, not review or authoring time.

The meaningful separation was teaching readiness:

| Record | Current position | Source-bound teaching evidence | Four-query result in this probe | Estimated quality/cost |
|---|---|---|---|---|
| `9af68e46cf69` | approved, normal draw, `approved_originals_need_parameters` | callable strict grammar, two witnesses, two rivals, and `lesson_identifiable`; retained repair/census evidence | 4/4 queries identifiable from the same 3 demonstrations | **High**: strong evidence and no observed Racket/dedup friction; still lacks a parametric prototype |
| `46c02325ed3b` | approved, normal draw, `approved_originals_need_parameters` | retained notes report canonical/Racket and lesson audits, but the selected source exports no semantic competitor or lesson checker | not testable with a source-bound checker in this probe | **Medium**: runtime cost was low, but one checker/preflight step is needed before parameter authoring can make a comparable claim |
| `01f4294de005` | unapproved, outside normal draw, `other_unapproved` | no exported lesson checker; two retained `needs_triage` audits report the generated blank-row shortcut (5,000/5,000 ordinary draws) against canonical examples | not testable; unresolved repair issue precedes parameter work | **Low for parameter authoring / high for repair priority**: cheap execution does not offset the known distribution defect |

“High/medium/low” is an ordinal estimate from this three-record sample, not a
corpus score. All three catalog/derived weights are `1.0`; provenance and equal
weight did not predict teaching readiness. No ARC-GEN or RE-ARC record was
sampled, so this ticket supports no quality claim about either source.

## One alternative allocation

For a shadow experiment, replace a flat parameter-authoring choice with a
**readiness-gated allocation**:

1. Give two owner slots to approved originals that already expose a strict
   grammar plus a callable demonstration-only lesson checker.
2. Give one owner slot to an approved original with strong retained evidence
   but no callable checker; the first deliverable is the checker, and parameter
   authoring proceeds only if it passes.
3. Route records with unresolved source-bound distribution findings to the
   repair lane; do not charge their repair time to the parameter-prototype
   success rate.

On this sample that is a `2:1:0` parameter-slot allocation for
`9af68e46cf69 : 46c02325ed3b : 01f4294de005`, with `01f4294de005` receiving a
separate repair slot. This is an experiment proposal, not a production policy
change or an approval decision.

## Bounded test and stopping rule

Run a ticket-seeded shadow comparison on at most **12 records or 180 authoring
minutes**, whichever comes first. Select six records by the current owner queue
and six by the readiness gate, source-bind every record, and cap each attempt at
15 minutes plus one protected-Racket batch of 3 demonstrations and 4 distinct
queries.

Count an attempt as usable only when all seven inputs are lawful and distinct,
all seven exact Racket labels succeed, and a demonstration-only checker rejects
all declared rivals on each of the four queries. Record authoring minutes,
generation attempts, duplicate rejections, Racket seconds, and unresolved
review findings.

Adopt the alternative for a larger trial only if it yields at least **two more
usable episodes per six attempts** than the current queue, without increasing
unresolved safety/grammar findings. Stop early if either arm has two
source-identity failures, any hidden-label/public-projection leak, or the
alternative falls behind by two usable episodes after four paired attempts.

## Coverage gaps

The probe did not author variants, rerun retained large censuses, or establish
unique program identification. It did not sample ARC-GEN or RE-ARC. The
`46c02325ed3b` lesson claims are retained evidence rather than a callable check
rerun here, and the `01f4294de005` shortcut is a retained reviewer finding, not a
new 5,000-sample replay.
