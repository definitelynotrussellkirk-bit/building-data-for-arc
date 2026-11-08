# Current notes: 1d1cffd62646

## Canonical family and repair

Original family: `training:5c2c9af4`. Three equally spaced, same-color dots define
the center (middle dot) and square-ring spacing (Chebyshev distance to either
endpoint). Draw all concentric square outlines, clipping them at grid edges.
The canonical Racket source is unchanged, SHA-256
`fe733c91003d5dc3fae0319eb38e4f28117e81865fdb168346b61281bff2b946`.

The old v1.1.1 sampler emitted only two vertically aligned dots. Its checker
rejected the original three-dot examples, and advertised spacing/color controls
were ignored. That restricted distribution never taught midpoint selection from
the original three-dot configuration. Version 1.2.0 restores three-dot inputs,
with horizontal, vertical and both diagonal directions. It honors `grid_h`,
`grid_w`, `step`, `dot_color` and `orientation`; unsupported legacy decorative or
degenerate controls fail explicitly. Old seeds intentionally yield new inputs.

Exact dimensions support 10..30, dot spacing 2..6 where the triple fits, and
colors 1..9. Booleans and non-integer numeric controls are rejected. `None`
retains the existing unpinned-axis convention. Impossible pinned directions fail;
unpinned directions/dimensions are chosen to accommodate requested spacing.
Validation accepts other equally spaced collinear slopes with the same contract;
the sampler covers only its four declared directions.

## Separate proposed parameter family

`workspace/parametric/` contains runnable generation, saved-batch verification,
an adapter and a promotion contract. `ring_stride=1` is the exact canonical
program. `ring_stride=2` retains the center and odd positive rings, preserving
the first ring through the endpoint dots. This changes output geometry while
retaining the original center/spacing/clipping reasoning.

Counts are independent: 2..8 demonstrations and 1..8 queries. Defaults retain
two demos and four distinct queries, including a 30x30 query. Inputs are matched
across settings for the same seed/count request. The demonstrations identify the
chosen setting against 22 declared hypotheses before any query target is used.
These finite rivals do not prove universal uniqueness. Labels from the prototype
CLI are matching-Racket executions; adapter labels are claims for later protected
qualification. Both lawful parameter programs were replayed on every retained
pair. Public IDs hash only visible bytes, with all private fields kept apart.

## Evidence and remaining scope

Changed-scope checks: 20 standard-library tests, all four original labeled pairs,
four generated step-6 orientation witnesses, one production two-demo/four-query
lesson (six unique inputs, no recorded rejections), and two parameter episodes
with four queries each. The production lesson and parameter episodes distinguish
the chosen rule from the declared rivals using demonstrations only.

Independent review covered count/spacing boundaries and export/certificate
rejection paths. It found an unserializable private-note failure that left a
partial destination. The writer now serializes all payloads before directory
creation; its regression failed before the fix and passes afterward. This is
not a general rollback promise for later filesystem failures.

Compact task-local evidence is in `workspace/parametric/evidence/current/`;
the returned `checks/` also retains exact commands, pre-repair failures, Racket
receipts and the independent review. Broad production batteries and protected
parameter qualification were not run. Source review, parameter acceptance and
training admission remain separate. Next useful step: accept/review the canonical
repair, then qualify the proposed adapter against its source inventory if desired.
