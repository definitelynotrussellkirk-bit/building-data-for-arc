# Blind solve notes — 3ef5f8be2639

## Observations

Each output is a solid rectangle of color 8 on an otherwise zero grid. Let `G` be the
single color-3 cell and choose the relevant color-2 cell `R`.

The output rectangle is exactly the intersection of the clipped 3×3 neighborhoods
centered on `G` and `R`:

- train 0: `G=(1,3)`, selected `R=(1,2)` -> rows 0..2, columns 2..3;
- train 1: `G=(2,5)`, `R=(4,4)` -> row 3, columns 4..5;
- train 2: `G=(3,2)`, selected `R=(2,2)` -> rows 2..3, columns 1..3.

Equivalently, before clipping the rectangle has height `3-|dr|`, width `3-|dc|`,
and is centered halfway between the two markers.

## Marker selection

When there are multiple red cells, the examples select the closest one to the green
cell. Train 0 has a distance tie and selects the row-major-earlier (left) red cell.
I therefore use minimum Chebyshev distance, then Manhattan distance, then row-major
order. The visible queries do not hinge on the tie rule: query 0 has one red, and in
query 1 the row-major-first red is also uniquely nearest.

## Predictions

- query 0: overlap is the single cell `(4,3)`;
- query 1: overlap is rows 3..4 and columns 2..3 (a 2×2 block).

No generator source, Racket rule, private labels, reference solution, or prior solve
notes were consulted.
