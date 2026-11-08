# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private
labels, previous solve notes, or audit evidence before this blind solve. I used
only the visible `challenge.json` examples and the packet's visible checker.

## Revision 0 — establish a failing baseline

The provided `solution.py` raises `NotImplementedError`. I am running the visible
checker unchanged first so the test is known to detect the missing behavior.

## Hypothesis for revision 1

For every nonzero color, the two input cells are opposite corners of an
axis-aligned rectangle. The output preserves the grid dimensions and fills the
inclusive row/column bounding box of those two cells with that color. Evidence:

- train 0: each diagonal pair expands to a 2×2 block;
- train 1: color 6 expands from `(1,6),(3,9)` to a 3×4 rectangle, color 5 to
  a 6×2 rectangle, and color 7 to 2×2;
- train 2: the same rule independently produces the 3×2 and 4×4 blocks.

The demonstrations do not distinguish what to do with a color occurring other
than twice or with overlapping rectangles. The generated queries retain two
cells per color and disjoint boxes, so the minimal visible rule is to fill each
observed nonzero color's bounding box.
