# Solve notes

## Visible-example hypothesis

The input consists of separated monochrome objects. Object position and source
color do not determine the answer; the output preserves each object's cells and
recolors the whole object according to reflection symmetry inside its tight
bounding box.

Observed mapping from the three demonstrations:

- symmetric left-right **and** top-bottom -> 2;
- symmetric left-right only -> 3;
- symmetric top-bottom only -> 4;
- neither reflection symmetry -> 6.

This accounts for the 2x2 squares and hollow 3x3 ring (both -> 2), upright
T-like masks (left-right only -> 3), sideways/top-bottom masks (top-bottom only
-> 4), and stair/L masks (neither -> 6). I implemented connected-component
extraction, normalized each mask to its tight bounding box, tested both
reflections, and repainted the original coordinates.

## Query predictions

Query 1 contains all four classes: ring -> 2, upright T -> 3,
up-down-symmetric zigzag/crown -> 4, stair -> 6. Query 2 contains a square -> 2,
a left-right-symmetric cap -> 3, and a diagonal stair -> 6.
