# Solve notes

Human work log based only on `solve/challenge.json` during this solve phase.

## Hypothesis

The two color-9 cells are translation anchors.  Order them row-major and use
the displacement from the first to the second as a copy vector.  Remove both
anchors, retain every other colored payload cell, and add a translated copy;
translated cells outside the original canvas are clipped.

Visible checks:

- Train 1: anchor delta `(2, 4)` moves the three-cell 3-shape mostly beyond the
  right edge; only the translated cell at `(3, 6)` remains visible.
- Train 2: delta `(2, 1)` moves the bottom payload down/right; only its top
  translated row survives clipping at the lower edge.
- Train 3: delta `(0, 7)` copies the left payload to the right edge exactly.

I implemented that rule directly, preserving payload colors independently.
No reference solution, generator source, Racket source, or private label was
consulted during this episode.  I had prior rule exposure from the generator
review, so this is an exposed—not blind—solve.
