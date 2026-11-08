# Solve work log

## Isolation and prior exposure

This is the required blind-before-repair episode. Before solving I had opened only
packet-level instructions and the assignment text. I did not open this task's
generator, canonical rule, reference solution, notes, audit records, or private
labels, and I had no earlier rule exposure that I am aware of.

## Revision 1 — complete the rectangle

**Visible pattern.** Every training input contains exactly three equal-colored
nonzero cells. Their coordinates occupy two rows and two columns, with one of the
four Cartesian-product positions absent. The output preserves the grid and fills
that missing position with the same color. For example, the first pair has
(0,0), (1,0), and (1,6), so output adds (0,6).

**Hypothesis.** The task completes the missing corner of an axis-aligned rectangle
whose other three corners are marked.

**Implementation.** Count nonzero occurrences by row and column. In a valid
three-corner L, the row used once and the column used once intersect at the missing
corner. Copy the input and paint that cell with the nonzero color.

**Alternatives considered.** Copying the adjacent arm, reflecting one point across
the elbow, and completing a 2x2 square all fit subsets of the examples, but the
large row/column separations show the intended object is a general rectangle.

**Expected test outputs.** For the first query add color 7 at row 0, column 0. For
the second add color 8 at row 1, column 0. Remaining uncertainty is limited to
whether background is always color 0; all visible examples support that convention.
