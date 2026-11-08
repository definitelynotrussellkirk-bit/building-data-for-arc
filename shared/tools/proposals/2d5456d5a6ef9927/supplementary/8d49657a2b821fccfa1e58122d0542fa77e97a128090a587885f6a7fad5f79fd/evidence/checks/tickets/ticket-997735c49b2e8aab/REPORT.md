# Allocation-quality ticket report

**Ticket:** `ticket-997735c49b2e8aab`  
**Consumer:** `bounded_owner_allocation_experiment_proposal`  
**Status:** completed, with no policy or admission change

## Source binding

The pinned anchor `033db13a9d37` still matches generator SHA-256
`9a6756b67c901b2e0b973c4c2dd30524d20f364f6af1a556b6cfb33f4fbcdda4`
and rule hash `3773168d1737`. `TRAINING-CONTEXT.md` is treated as a dated
October 23, 2026 report (SHA-256
`09f78a6ca711073fd70e21fb19fb93c5714200392697271a8a705a370b88bf49`),
not as live per-record evidence.

The ticket seed deterministically selected:

| Record | Current state | Useful evidence | Main gap |
|---|---|---|---|
| `a5e17b975ae0` | approved, weight 1 | four exact axes, declared rivals/witnesses, task tests, retained 1,200 production and 2,000 cyclic checks | no current four-query receipt or parameter workspace |
| `c2cd365ed4fa` | approved, weight 1 | six exact axes; Racket, override, connectivity, and impostor tests | no review index, lesson competitors, four-query receipt, or parameter workspace |
| `generic_waypoint_route_gen2` | unreviewed, weight 0 | retained protected-Racket fixture with 3 demonstrations and 4 queries | live API still emits 3 demonstrations and 1 query; manifest denies approval/admission |

The packet has 500 records: 293 approved, 498 at weight 1, two at weight 0,
and 205 positive-weight records that are not approved. That catalog shape is an
observation, not evidence that any individual positive-weight record is defective.
No sampled record was source-specific ARC-GEN or RE-ARC, so their dated aggregate
shares are not used to rank quality.

## Bounded alternative

Run a **shadow experiment only** over 20 future assignments: 10 current-policy
and 10 evidence-stratified. The alternative arm contains four approved records
without four-query evidence, three approved records with strong lesson evidence
but no parameter workspace, two unapproved/weight-zero variants with a concrete
API or admission gap, and one existing evaluation-focus record. Freeze source
and rule hashes, retain failures, allow at most two episode attempts per record,
and optionally label one paired setting for the two strongest alternative
records.

The design costs exactly 70 base labels (`10 × (3 demos + 4 queries)`) and at
most 14 paired-setting labels. Adopt no allocation change unless qualified yield
per reviewer hour improves by at least 10%, Racket seconds per qualified episode
do not worsen, every stratum has a success, and at least 7/10 alternative records
yield qualified episodes. Stop early on label/source drift or two newly introduced
canonical-domain regressions. Otherwise retain current policy or report the test
inconclusive.

## Limits

This was one deterministic three-record inspection with no new generator draws,
Racket labels, model jobs, corpus census, or dataset export. It cannot estimate
an optimal mixture or corpus-wide benefit. Full structured evidence is in
`result.json`; the exact probe command is in `command.json`.
