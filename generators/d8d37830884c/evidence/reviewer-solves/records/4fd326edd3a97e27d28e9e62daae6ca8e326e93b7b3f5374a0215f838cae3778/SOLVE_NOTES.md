# Solve notes

## Visible evidence

- All outputs preserve the input dimensions and zero background.
- Every nonzero input cell remains occupied, but its original color is replaced by 1 or 2.
- In train 0, both six-cell gray components become 2; the singleton and larger lower components become 1.
- Train 1 repeats the distinction across several shapes: cardinality six, not shape or position, predicts 2.
- Train 2 breaks the possible gray-only shortcut: three color-6 components of six cells become 2, while color-7 components of other sizes become 1.
- Components must be same-color and 4-connected; diagonal contact is not enough to merge cells.

## Hypothesis

Find each same-color 4-connected nonzero component. Recolor exactly-six-cell components red (2), and every other nonzero component blue (1), leaving background zero.

## Implementation

The solution flood-fills each component once, counts its cells, then writes the corresponding label into a fresh output grid. It does not mutate the input.
