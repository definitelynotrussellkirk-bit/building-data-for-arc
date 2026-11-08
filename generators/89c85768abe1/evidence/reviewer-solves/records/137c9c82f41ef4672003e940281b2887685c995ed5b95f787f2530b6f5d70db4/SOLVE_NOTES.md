# Solve notes — visible examples only

This is a human work log. I had already seen the task rule while repairing the
generator, so this is not blind; I did not consult the generator, Racket rule,
reference solution, private labels, or the preserved earlier solve during this
episode.

## Hypothesis 1

For each nonzero color, locate its two cells and fill the inclusive axis-aligned
bounding rectangle between them with that color. Leave zero cells outside those
rectangles unchanged.

Visible checks:
- Train 1: color 4 spans rows 1–6 and columns 9–10; color 2 spans rows 6–7 and
  columns 0–4. The output fills exactly those rectangles.
- Train 2 contains both diagonal directions: color 7 spans a 3×2 rectangle,
  color 1 spans a 3×2 rectangle with the opposite diagonal orientation, and
  color 6 spans a 2×2 rectangle. All are filled by bounding box.
- Train 3 similarly fills a tall 8×4 rectangle for color 7 and a 2×4 rectangle
  for color 9.

No competing visible rule explains the interior fills more simply. I will test
one implementation of this rule against all three demonstrations.
