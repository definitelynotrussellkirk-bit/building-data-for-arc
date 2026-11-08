# Working notes: 7768dfc99e25

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7768dfc99e25/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D1 — Repair object-level border validation (2026-10-24)

**Decision.** Validate 4-connected color-2 components rather than counting
border and interior cells. Require at least two red components and exactly one
red component touching the outer border.

**Reason.** The prior checker accepted one L-shaped object spanning border and
interior, despite the declared single-object degenerate, and also accepted two
separate border-touching red objects. Both concrete regressions are now retained.

## D2 — Episode-fixed target-color prototype (2026-10-24)

**Decision.** Add a separate proposed family with `target_color` in `{2,3}`.
Color 2 is the exact canonical Racket program; color 3 preserves component
segmentation, border selection, and bounding-box crop. Every matched input has
one border component and an interior distractor for both candidate colors, so
labels—not input distributions—identify the setting.

**Boundary/export evidence.** Requests support 2–6 demonstrations and 1–8
queries independently. The first four query sizes are 12×14, 18×20, 24×24, and
30×30; the largest has substantive content touching all four boundaries.
Protected Racket executed 28 labels across both settings and seeds 0/17. Four
saved public challenges passed the strict public-only checker. The bounded
adversarial pass covered malformed settings, min/max request counts, the two
component regressions, and the 30×30 boundary case.

**Disposition and limit.** Proposed and manifested, not accepted. Native
qualification stops at `Production generator must be approved on its current
source/rule` because the validator repair changed canonical generator bytes.
Owner reapproval is the next action. Decorative source axes remain outside this
focused repair; no claim is made that the historical scalar generator now has a
fully honest broad axis contract.
