# Solve work log

## Exposure declaration before solving

I had not opened task `d1bf9a8e4c69`'s generator, Racket rule, reference
solutions, private labels, audit records, or previous solution explanations. I
used only `solve-blind/challenge.json` and the visible-only checker.

## Revision 1 — connected-component bounding-box corners

Across all three training examples, every nonzero 4-connected component is
replaced by the four corner cells of its axis-aligned bounding box, retaining
its color and the original canvas size. Interior cells and non-corner boundary
cells are cleared. Components are processed independently, including separate
components that share a color.

Examples supporting the rule:

- The six-cell color-3 zigzag in training example 1 spans rows 2–4 and columns
  0–3; the output contains color 3 exactly at `(2,0)`, `(2,3)`, `(4,0)`, and
  `(4,3)`.
- The first color-9 component in training example 2 spans rows 6–7 and columns
  1–3; its output is the four corners of that 2-by-3 box. The second color-9
  component is handled separately.
- Both objects in training example 3 obey the same operation despite different
  colors and shapes.

I implemented a 4-neighbor flood fill by color, measured each component's row
and column extrema, and emitted its four corners. Degenerate one-row or
one-column boxes naturally collapse duplicate corners to the appropriate one or
two cells. The main residual uncertainty is whether diagonal touching should
join objects; the training data consistently presents ordinary 4-connected
objects, so 4-connectivity is the least-assumptive choice.
