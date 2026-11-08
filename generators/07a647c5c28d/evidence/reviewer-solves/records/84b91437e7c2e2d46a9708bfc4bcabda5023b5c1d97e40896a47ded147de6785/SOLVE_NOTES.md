# Solve work log

## Exposure statement

Before this solve I had not opened the selected task's generator, rule, notes,
reference solution, private labels, or audit evidence. I used only the visible
examples printed by `python3 review.py blind prepare` and the checker feedback.

## Revision 1 — baseline diagnostic

The supplied `solution.py` raised `NotImplementedError`. I ran one explicit
`diagnostic_probe` to establish a failing baseline before changing behavior. It
failed by execution error on all three visible examples, as expected.

## Revision 2 — crop around color 6

Hypothesis: color 6 identifies the object whose axis-aligned bounding rectangle
is returned. The crop preserves every input cell inside that rectangle, even if
another color is disconnected from the color-6 cells.

Evidence from the visible examples:

- Example 0: the two diagonal 6 cells have a 2×2 bounding box, exactly matching
  the output.
- Example 1: the 6 cells span a 5×3 box; three color-4 cells inside that box are
  retained, while the separate color-1 object is omitted.
- Example 2: the 6 cells span rows 1–4 and columns 1–6; the color-4 cell inside
  that rectangle remains, while the separate color-5 domino outside is omitted.

Implementation: locate all cells equal to 6, compute min/max row and column, and
return that inclusive slice. The visible data always contains color 6; the code
returns a copy of the input only as a conservative total-function fallback for
an unsupported no-6 input.

Predicted query structure before checking:

- Query 0: a 2×3 crop around the diagonal 6 cells.
- Query 1: a 5×3 crop around the L-shaped 6 object, retaining the two color-2
  cells that lie inside the box.

Remaining uncertainty: the examples establish color 6 as the selector, but do
not test multiple disconnected groups of 6; the implementation uses their union
because the rule is stated over all color-6 cells and that is the least
assumptive extension.
