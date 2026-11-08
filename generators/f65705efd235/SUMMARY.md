# f65705efd235 — Rectangle Border from Four Corners

A 7–24 by 7–24 zero-background grid contains 2–6 distinct nonzero colors. Each color occupies exactly the four corners of one axis-aligned rectangle. The answer starts from a fresh zero canvas and paints every complete rectangle border in ascending color order, so a larger color overwrites a smaller one where borders intersect.

The four-position curriculum deliberately includes:

- canonical two-cell-wide or two-cell-high rectangles;
- a thick rectangle with a protected background interior cell, distinguishing outline from solid fill;
- overlapping borders, exposing ascending color order;
- both two-rectangle and more-than-two-rectangle scenes;
- exact canonical dimension/palette profiles in every difficulty band.

Caller controls are limited to exact observable axes: `grid_h`, `grid_w`, and `n_rects`. The generator is version `3.0.0` and pins canonical rule hash `635fcfe4fd6f`.
