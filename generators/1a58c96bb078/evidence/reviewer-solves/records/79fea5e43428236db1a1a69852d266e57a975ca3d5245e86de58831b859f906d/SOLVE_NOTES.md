# Solve work log

## Exposure

Before this solve I had not opened the task's generator, canonical rule, reference
solution, private query labels, audit records, or earlier solution explanations.
I saw only the public visible examples produced by `review.py blind prepare`.

## Revision 1 — column-header recoloring

**Hypothesis.** The first row is a sparse color key. Every gray cell (color 8)
below a nonzero first-row cell is recolored with that column's header color.
Gray cells in columns whose first-row cell is zero stay gray. All other cells,
including non-gray distractors below the header, remain unchanged.

**Evidence from the examples.**

- Example 0 has headers 9 and 3 in columns 4 and 5; exactly the gray cells in
  those two columns become 9 and 3. The lower color-6 cell is unchanged.
- Example 1 has headers in columns 0, 5, 6, and 8. All gray cells in those
  columns take the matching header color, while the gray cell in column 7
  remains gray and the color-4 distractors are untouched.
- Example 2 behaves the same for header columns 0, 1, and 6; gray cells in
  columns 5 and 9 remain gray.

This also distinguishes the rule from alternatives such as copying the nearest
colored cell or using every non-gray cell as a key: the lower distractors do not
recolor anything, and the changed cells align exactly by column with row 0.

**Implementation.** Copy the grid, scan rows below the first, and replace a cell
only when it is 8 and its first-row column value is nonzero.

**Predicted query behavior.** Query 0 recolors gray cells in columns 3, 6, and 10
with 5, 1, and 3. Query 1 recolors gray cells in columns 0 and 5 with 3 and 7;
the lower color-5 cell in column 3 remains unchanged.

**Remaining uncertainty.** No visible example places gray in the first row. The
implementation treats row 0 solely as the key and leaves it unchanged, which is
the simplest rule consistent with all examples.
