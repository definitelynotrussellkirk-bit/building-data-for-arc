# Solve work log

## Exposure declaration

Before this solve I had not opened the task's generator, canonical rule, reference
solutions, private labels, prior solution explanations, or the assigned repair
generator. I used only the visible examples printed by `review.py blind prepare`.

## Revision 1 — required failing baseline

The template still raised `NotImplementedError`. I ran the visible-only checker to
record a genuine failing baseline. It reported an execution error on all three
visible examples, as expected.

## Revision 2 — fill each color's bounding rectangle

Observation: every nonzero color occurs at two marker cells in each input. For each
color, the output fills every cell in the smallest axis-aligned rectangle containing
its two markers, including both endpoints. Examples checked manually:

- Example 0: color 5 spans rows 0–1 and columns 0–2, producing a 2×3 block.
- Example 0: color 8 spans rows 3–5 and columns 3–9, producing a 3×7 block.
- Example 2: color 1 spans rows 0–4 and columns 0–4, producing a 5×5 block.

The implementation groups all nonzero cells by color, computes row/column minima
and maxima, copies the input, and paints each inclusive rectangle. Grouping all
markers rather than assuming exactly two is a harmless generalization consistent
with the visible rule. The visible rectangles do not overlap; overlap precedence is
therefore untested and remains a domain assumption.
