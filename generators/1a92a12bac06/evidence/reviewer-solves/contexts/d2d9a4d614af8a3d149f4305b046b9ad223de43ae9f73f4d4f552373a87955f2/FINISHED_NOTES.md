# Visible-only solve notes

This is a human work log written after `solve_episode.py prepare`. I did not
open the generator, Racket source, canonical answers, or private labels during
this solve. I had earlier rule exposure from the required repair work, so the
final declaration must say `earlier-exposure yes`.

## Hypothesis

Each separated red (2) vertical component is treated independently. Preserve
its position and shape, then recolor its lowest `floor(component height / 2)`
red cells cyan (8). For odd heights, the upper middle cell remains red.

Visible checks:

- Train 0: heights 3, 6, 7, 6 produce 1, 3, 3, 3 cyan cells.
- Train 1 includes floating bars, so “measure upward from the grid floor” is
  false; the threshold is relative to each component's own bottom.
- Train 2 includes a height-7 top-aligned bar; only its bottom 3 cells change,
  distinguishing floor from ceil.

## Implementation

Find every 4-connected red component, compute its top and bottom rows, and
change component cells at or below `bottom - floor(height/2) + 1` to cyan.
All other cells are copied unchanged.
