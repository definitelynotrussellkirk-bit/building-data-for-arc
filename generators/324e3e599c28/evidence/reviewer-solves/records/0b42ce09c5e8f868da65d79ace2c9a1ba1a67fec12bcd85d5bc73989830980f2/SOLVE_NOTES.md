# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, canonical rule, reference solution, private
query labels, notes, audits, or any generator assigned for repair. I used only the
visible examples in `solve-blind/README.md` / `challenge.json`.

## Revision 1 — point reflection around color 9

**Observation.** Each example has one color-9 cell and one nearby nonzero shape.
The output keeps the input and adds a second copy on the opposite side of color 9.

**Hypothesis.** Color 9 is a point pivot. For each nonzero, non-9 cell at `(r,c)`,
add the same color at `(2*pivot_r-r, 2*pivot_c-c)`. This is a 180-degree rotation
about the pivot, not a line reflection.

**Visible probes.** In train 0, `(7,2)` relative to pivot `(6,4)` maps from
`(+1,-2)` to `(-1,+2)=(5,6)`, matching the added color 1. `(8,3)` maps to
`(4,5)`, also matching. In train 2, the four-cell vertical string below the pivot
maps to the four cells above it in reversed spatial order. Train 1 is consistent:
the right-side `[7,2,7]` maps to the left side of the pivot.

**Implementation.** Copy the grid, locate the unique 9, rotate every colored
non-pivot cell through it, and write in-bounds reflected cells. The code validates
a rectangular grid and a unique pivot. I preserve all input cells.

**Predicted queries.** Query 0 gains a 2x2 color-3 block at rows 6–7, columns 3–4,
opposite the original block across pivot `(5,5)`. Query 1 gains `[7,2,7]` at row 4,
columns 2–4, opposite the existing row segment across pivot `(4,5)`.

**Remaining uncertainty.** The visible examples do not show reflected cells leaving
the grid or conflicting with an existing different color. I chose conservative
in-bounds writes and otherwise preserve the input.
