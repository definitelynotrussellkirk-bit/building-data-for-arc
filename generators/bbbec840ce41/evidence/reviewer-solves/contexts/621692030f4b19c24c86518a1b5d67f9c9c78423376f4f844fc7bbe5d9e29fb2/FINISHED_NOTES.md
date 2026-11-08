# Visible-only solve notes

The output keeps every original nonzero cell and adds same-colored cells. The
coordinate relation is reflection across the anti-diagonal: in an `n x n` grid,
source `(r, c)` adds `(n-1-c, n-1-r)`.

Evidence from visible examples:

- Train 0, `n=8`: input color 2 at `(5,0)` adds color 2 at `(7,2)`; `(0,2)`
  adds `(5,7)`. These are anti-diagonal reflections, not a main-diagonal swap
  or 180-degree rotation.
- Train 1, `n=9`: color 5 at `(2,0)` adds `(8,6)`, while the source remains.
- Train 3, `n=12`: color 3 at `(4,1)` adds `(10,7)`, confirming the same map at
  a different grid size.
- Cells already on the anti-diagonal map to themselves, so they are unchanged.

Implementation copies the grid once and writes each nonzero source to its
anti-diagonal partner. It reads only the original grid, so newly written cells
do not trigger an unintended second pass.
