# d02691ffb818

A 0-background grid contains 2–14 blue (1) marker cells. The default curriculum
uses a deterministic three-slot cycle:

1. **canonical** — one of the four observed canonical shapes, 2–4 interior
   markers, and non-overlapping X stencils;
2. **edge** — at least one marker on the boundary, so the rule's in-bounds
   clipping is visible; and
3. **clustered** — at least one nearby marker pair, so same-color stencil union
   is visible.

The pinned rule emits a fresh same-size 0 grid. For every marker it paints orange
(7) at the marker and the four diagonal neighbours that remain in bounds.
Boundary markers and overlapping stamps are lawful. Public overrides are limited
to exact observable controls (`grid_h`, `grid_w`, and `markers`) and remain valid
in every difficulty band.

Kind: `per_puzzle`. Reviewed version: `2.3.0`. Rule hash: `3eec1d7807b1`.

## Teaching-domain boundary

The total Racket rule can execute arbitrary blue-marker patterns, but the reviewed
training grammar requires 2–14 markers and excludes an exact singleton, solid 2×2
marker block, or four-cell straight line. These are low-information mutation probes,
not evidence-rich lessons. Boundary clipping and nearby/overlapping X stamps remain
explicitly generated and accepted.
