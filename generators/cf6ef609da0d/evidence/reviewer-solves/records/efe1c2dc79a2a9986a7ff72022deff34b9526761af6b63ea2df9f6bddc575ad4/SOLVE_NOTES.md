# Solve notes

## Observations from the visible examples

- Inputs contain a black background (0) and several 4-connected purple (6) components.
- Outputs preserve the grid dimensions, erase most components to black, and recolor selected whole components red (2).
- In training example 0, the singleton at `(2,2)` is retained. A lower-left component has a bounding box that crosses the main diagonal but no occupied diagonal cell; it is erased. This rules out a bounding-box-intersection shortcut.
- In training example 2, the component containing `(7,7)` is retained in full, including its off-diagonal cells.
- Training examples 1 and 3 have no component with an occupied cell on the main diagonal, and their outputs are entirely black. This rules out retaining the component merely nearest to the diagonal.

## Inferred rule

Find every 4-connected component of color 6. Retain and recolor an entire component to color 2 exactly when at least one of its occupied cells satisfies `row == column`. Erase every other component to 0.

## Alternatives considered and rejected

- **Any component whose bounding box intersects the diagonal:** contradicted by the erased lower-left component in example 0.
- **The component closest to the diagonal:** contradicted by all-black outputs when no component actually touches the diagonal.
- **Only recolor the diagonal cells themselves:** contradicted by example 2, where all cells in the touching component are recolored.

## Implementation

The solver performs a breadth-first search over all 4-connected color-6 components, tests each component for an occupied main-diagonal cell, and paints qualifying components red in a fresh zero grid.
