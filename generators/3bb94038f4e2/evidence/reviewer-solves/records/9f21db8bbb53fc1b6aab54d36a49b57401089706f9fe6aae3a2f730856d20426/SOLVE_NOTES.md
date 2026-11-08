# Solve work log

## Exposure declaration before solving

I had not opened task `3bb94038f4e2`'s generator, canonical rule, private labels,
reference solution, audit material, or prior solve notes.  Before the assignment
was drawn I had read only packet-level documentation (`WELCOME.md`,
`RETURN-GUIDE.md`, `ARC-DESIGN.md`, `repo/AGENTS.md`, and `repo/README.md`).  None
identified this blind task's transformation.

## Revision 1 — horizontal alternating marker runs

**Visible pattern.** In every changed row, color 1 appears at columns separated
by exactly one zero: columns `1,3,5` in train 0 and 2, and `4,6,8` / `4,6,8,10`
in train 1.  The output fills every cell from the first marker through the last.
Rows with spacing three (`0,3,6` or `3,6,9`) remain unchanged, as do adjacent
pairs, isolated cells, and the colored distractor objects.

**Hypothesis.** For each maximal horizontal run containing at least three color-1
markers with consecutive column difference 2, replace the alternating span by a
solid color-1 segment.  Preserve all other cells and colors.  I used maximal
runs rather than requiring all 1s in the row to participate, so an unrelated 1
would not invalidate a genuine run.

**Predicted queries.** Query 0 should fill row 5, columns 3–7.  Query 1 should
fill row 6, columns 1–5.  The spacing-three rows and the two-marker row should
remain unchanged.

**Alternatives considered.** “Fill between any three equally spaced 1s” is too
broad because the spacing-three examples are explicit negatives.  “Fill the
topmost matching row” is contradicted by train 1, where two lower rows change.
“Fill every pair separated by one zero” is contradicted by query 0 row 7 and is
not supported by training; the demonstrations consistently require at least
three markers.

**Remaining uncertainty.** The examples do not establish behavior for a row
with multiple disjoint qualifying runs or an unrelated 1.  The implementation
uses independent maximal runs, which is the least destructive extension of the
visible rule.
