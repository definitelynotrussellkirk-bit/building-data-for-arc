# Solve work log

## Exposure declaration before solving

I had not opened the assigned repair generator, this blind task's generator, any
Racket rule, private labels, prior solution notes, or reference solution. I had
only read the packet workflow and `solve-blind/challenge.json`.

## Revision 1 — orthogonally adjacent 2/3 pairs

**Hypothesis.** A color-2 cell and color-3 cell that share an edge form a pair.
Every participating 2 is erased to 0, and every participating 3 is recolored 8.
Cells not in such a pair—including 2/3 cells separated by a gap or touching only
diagonally—and all color-5 cells are unchanged.

**Visible evidence.** In training example 1, each horizontal `2,3` pair becomes
`0,8`. In example 2, the same happens to vertical pairs. Example 3 establishes
that order is irrelevant (`3,2` becomes `8,0`) and that an extra same-color cell
next to a consumed pair is left alone unless it itself touches the opposite
color.

**Implementation.** Scan the original grid, mark both endpoints of every
orthogonal 2/3 adjacency, then apply all changes simultaneously. This avoids
scan-order effects for overlapping pairs.

**Predicted queries.** Test 1 changes the horizontal pair at row 1, columns 1–2
and the vertical pair at rows 8–9, column 1. Test 2 changes four vertical pairs
at column 3 (rows 0–1), column 5 (rows 3–4 and 7–8), and column 0 (rows 6–7).
The diagonal 2/3 near rows 3–4 remains unchanged.

**Alternatives rejected.** The rule is not “change every 3 near any 2 within a
larger radius,” because visible gap-separated and diagonal cells remain. It is
not direction-specific because both horizontal orders and vertical pairs appear.

**Remaining uncertainty.** None material for the visible examples; hidden cases
may contain overlapping chains, handled by simultaneous endpoint marking.
