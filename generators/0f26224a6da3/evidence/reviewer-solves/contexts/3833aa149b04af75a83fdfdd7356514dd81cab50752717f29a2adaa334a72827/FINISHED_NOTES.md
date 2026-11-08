# Solve work log

## Earlier exposure

I had not opened this task's generator, Racket rule, reference solutions, private
query labels, audits, or prior solution notes. I used only the visible challenge.

## Hypothesis

Each nonzero cell is tested against its four orthogonal neighbors in the **input**.
If all four in-bounds neighbors are background, that isolated cell grows into a
same-colored plus: center, up, down, left, and right, clipped at grid edges.
A cell with any orthogonally adjacent nonzero cell stays unchanged. Diagonal
contact does not prevent growth.

Evidence from the examples:

- The horizontal 9 pair in train 0 and vertical 4 pair in train 2 stay unchanged.
- The diagonal 7 cells in train 0 both grow and their pluses overlap.
- Every isolated singleton grows to five cells except at a boundary, where the
  clipped plus has four cells.

I interpret adjacency by occupancy rather than by matching color. This matters in
test query 0, where 9 and 3 touch horizontally: under this hypothesis both remain
unchanged. The visible training pairs do not directly contrast occupancy-based
adjacency with same-color adjacency, so this is the main remaining uncertainty.
The occupancy interpretation is the simpler local rule and avoids two differently
colored pluses overwriting one another's original centers.

## Probe and implementation

I first wrote a visible-example regression script and ran it against the untouched
skeleton. It failed at `NotImplementedError`, confirming the test exercised the
missing behavior. I then implemented the local rule using the original grid to
decide isolation and a copied grid for additions. Existing nonzero cells are never
overwritten.

The implementation passes all three visible training examples. I stopped after the
packaged visible-only checker also passed, because private query correctness is
intentionally withheld.
