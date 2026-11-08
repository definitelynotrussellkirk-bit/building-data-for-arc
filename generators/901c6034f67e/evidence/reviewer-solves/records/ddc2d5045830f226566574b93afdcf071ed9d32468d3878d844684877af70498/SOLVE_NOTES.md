# Solve notes — 901c6034f67e

This is the required **post-repair exposed solve**. I had already reviewed the
rule while repairing the generator, so this episode is not blind. During this
solve episode I consulted only `solve/challenge.json`; I did not open the
Racket authority, generator source, reference solutions, or private labels.

## Visible-example hypothesis

Each nonzero monochrome 4-connected component keeps its exact cells but receives
a rank color. The ranking statistic is the number of component cells that lack
at least one orthogonal same-component neighbor (the count of contour cells),
ascending. Rank colors are 2, 3, and 4. A top-left positional tie-break is a
reasonable deterministic completion, although the visible examples use distinct
counts.

Evidence from the three demonstrations:

- A 2x2 block has four contour cells and receives 2 before a 2x3 rectangle
  (six contour cells) and a 3x3 rectangle (eight contour cells).
- A length-5 line receives 2; a 5x3 rectangle has 12 contour cells and receives
  3; a length-14 line receives 4. This distinguishes contour count from area.
- A length-3 line receives 2; the bent object receives 3; the 5x3 rectangle
  receives 4. Input colors 2/3/4 are not already the desired ranks.

## Implementation

Find same-color 4-connected objects, count contour cells against the object's
own occupied set, sort ascending by `(contour_count, top_left)`, and repaint on
a zero grid with rank colors. This is attempt 1.
