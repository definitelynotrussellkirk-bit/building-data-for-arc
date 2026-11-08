# Solve work log

## Exposure declaration before solving

I had not opened the Racket rule, either generator, private query labels,
reference solutions, earlier solution explanations, or audit evidence. I used
only the visible examples in `README.md` / `challenge.json` and local Python.

## Revision 1 — nearest-corner rectangle

The input is otherwise color 8 and contains one marker. Each output fills the
inclusive rectangle between that marker and one grid corner:

- 17×13, marker `(8,6)`: the 9×7 top-left rectangle is filled. Both axes tie,
  so this example establishes top/left tie-breaking.
- 18×10, marker `(17,4)`: the 1×5 bottom-left rectangle is filled.
- 11×11, marker `(7,2)`: the 4×3 bottom-left rectangle is filled.

Hypothesis: independently choose the nearer vertical boundary and nearer
horizontal boundary, resolving a tie toward top or left, then fill the inclusive
rectangle to that corner with the marker color. The implementation preserves the
shape and all cells outside the rectangle. Remaining uncertainty is limited to
inputs outside the visible one-marker-on-8 domain; the solver rejects those
rather than inventing behavior.
