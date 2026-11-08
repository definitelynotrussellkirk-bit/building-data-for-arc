# Solve work log

## Exposure declaration before solving

I had not opened task `14042d4b8317`'s generator, Racket rule, notes, prior
solutions, audit records, or private labels. I had also not opened the assigned
repair generator. I used only `solve-blind/challenge.json`.

## Revision 1 — complete each monochrome rectangle

**Observation.** In every visible training pair, each nonzero color appears at
three corners of an axis-aligned rectangle. The output preserves all cells and
adds the one missing corner in the same color. The rule applies independently
when two colors occur in one grid.

Examples checked manually:

- Azure: `(0,8), (3,4), (3,8)` gains `(0,4)`.
- Red and gray each form separate three-corner rectangles and each gains its
  fourth corner.
- Blue: `(8,1), (8,4), (15,1)` gains `(15,4)`.

**Implementation.** Group non-background cells by color. For any group with
exactly three cells, two distinct rows, and two distinct columns, compute the
2-by-2 Cartesian product and fill its unique missing coordinate. Preserve all
other cells unchanged.

**Predicted test changes.** The first query gains magenta at `(10,3)`. The
second gains blue at `(8,8)` and gray at `(5,10)` (zero-indexed).

**Alternatives considered.** Reflection of a lone point across the diagonal
pair is equivalent on these examples, but the Cartesian-product formulation is
simpler and makes the independent-per-color behavior explicit. I did not infer
any row/column ordering dependence.

**Remaining uncertainty.** The visible examples do not establish behavior for
more than three cells of one color, collisions, or non-rectangular groups. The
implementation deliberately changes only the exact demonstrated 3-corner case.
