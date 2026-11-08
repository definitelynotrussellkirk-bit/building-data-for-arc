# Blind solve notes — 51db77fe24c5

## Visible pattern

Each training input contains several disconnected blue (`1`) objects. The only
cells changed are one four-cell object shaped as a filled 2×2 square; those four
cells become red (`2`). Other four-cell objects (zigzags/T-like shapes) remain
blue, so cell count alone is insufficient.

## Hypothesis

Find each 4-connected blue component. Recolor every component whose exact cell
set is the Cartesian product of two adjacent rows and two adjacent columns—that
is, an isolated filled 2×2 square. Leave every other cell unchanged.

The first query visibly contains two such isolated squares, so the solver applies
the rule to every matching component rather than selecting only one.

## Implementation probe

Implemented component extraction with 4-neighbor connectivity, then required:

- component size = 4;
- exactly two rows and two columns;
- all four row/column combinations present.

This distinguishes the target square from same-sized zigzag and T objects.
