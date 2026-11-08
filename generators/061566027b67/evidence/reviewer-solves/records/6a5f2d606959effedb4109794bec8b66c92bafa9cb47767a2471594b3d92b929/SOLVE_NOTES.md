# Solve work log

I had no earlier exposure to task `061566027b67`, its generator, or its Racket rule. I used only the visible challenge prepared in `solve-blind/`.

## Revision 1 — largest solid rectangle amid noise

All three demonstrations are 16×16 noisy multicolor grids. In each, one color contains a conspicuous filled rectangle of area 12, sometimes with an adjacent same-color distractor:

- example 0: color 4 at rows 1–3, columns 0–3 (3×4), while an extra 4 touches its right edge;
- example 1: color 6 at rows 6–11, columns 14–15 (6×2);
- example 2: color 4 at rows 7–9, columns 4–7 (3×4), amid additional color-4 noise.

The output erases every other cell and preserves only that rectangle at its original location and color. I therefore search every nonzero color for the largest completely filled rectangle whose two dimensions are at least 2, then copy only that rectangle to an all-zero output grid. The two query predictions are a 2×6 color-1 rectangle at rows 6–7, columns 1–6, and a 3×4 color-8 rectangle at rows 11–13, columns 10–13.

Remaining uncertainty: the demonstrations all use area 12, so the hidden rule could explicitly target a 12-cell rectangle rather than the largest 2-D solid rectangle. The latter is the less overfit formulation and still selects the same structures in every visible example and query.
