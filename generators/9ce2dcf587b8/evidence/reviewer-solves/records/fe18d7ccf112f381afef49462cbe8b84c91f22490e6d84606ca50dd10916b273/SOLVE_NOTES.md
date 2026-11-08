# Solve work log

## Exposure declaration

Before solving I had not opened this task's generator, Racket rule, notes,
solutions, private query labels, or audit evidence. I used only the visible
examples created by `python3 review.py blind prepare` and my own test script.

## Revision 1 — union of full X-lines

**Hypothesis.** Every nonzero input cell is a seed. Draw both 45-degree diagonals
through each seed all the way to the grid boundaries, using the common seed
color. The output is the union of these diagonal lines on the original-size grid.

**Evidence.** In training example 0, the seed at `(1, 2)` produces exactly the
NW, NE, SW, and SE rays visible in the output. In example 1, the output is the
union of the two X-lines through `(3, 3)` and `(13, 7)`, including their overlap.
The three seeds in example 2 likewise account for every colored output cell, and
the single seed in example 3 gives a symmetric boundary-truncated X.
Algebraically, a cell is colored iff for at least one seed `(sr, sc)`,
`abs(r-sr) == abs(c-sc)`.

**Alternatives rejected.** Joining seeds pairwise would not explain the complete
four-way rays in the one-seed examples. Extending only toward the nearest edge
or stopping at intersections would omit observed cells. Horizontal/vertical
rays are absent.

**Test record.** `WORK/checks/blind_visible_examples_test.py` was first run
against the provided `NotImplementedError` skeleton and failed as expected. This
revision then implements the diagonal predicate and is checked against all four
visible training pairs before the official visible-only checker.

**Remaining uncertainty.** All visible inputs use one foreground color. The
implementation therefore treats mixed-color inputs as outside the demonstrated
contract rather than inventing an overlap precedence rule.
