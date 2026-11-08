# Solve notes

## Visible-example hypothesis

Each transformation searches the **original input** for two equal nonzero cells
that are diagonally adjacent, hence opposite corners of a 2x2 square. It paints
all four cells of that square with the pair's colour. Existing cells of another
colour in the other corners are overwritten; unequal-colour diagonals do not
trigger.

Evidence from the three visible examples:

- Example 0: colour 4 at `(5,3)` pairs diagonally with `(6,2)` and `(6,4)`, so
  the two overlapping 2x2 squares form a solid 2x3 block. The 6 at `(5,2)` is
  overwritten, while the unrelated 6 at `(5,5)` remains.
- Example 1: the three 5s at `(2,5)`, `(2,7)`, `(3,6)` likewise form two
  overlapping diagonal pairs. The 8 at `(3,7)` is a companion corner and is
  overwritten. Isolated 5, 7, and 8 cells remain.
- Example 2: the three 8s at `(1,4)`, `(2,3)`, `(2,5)` create the 2x3 block;
  the 9 at `(1,3)` is overwritten, while the unequal 8/9 diagonal near column
  6 does not activate.

## Implementation choice

I freeze the input coordinates, collect colours in first visible row-major
order, and fill every matching downward-left or downward-right adjacent pair
into an output copy. Freezing the source prevents newly painted cells from
creating further pairs. The visible examples do not expose a conflict between
two different triggering colours in one square; row-major colour order is a
stable tie-break for that unobserved case.
