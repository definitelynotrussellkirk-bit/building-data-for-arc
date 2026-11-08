# Visible-only solve notes

## Observation

Each input has black `0`, gray `5`, and one other color appearing exactly twice.
The output deletes every gray wall and every unused open cell, retaining a
4-connected route in the repeated color between the two marked cells.

The first training pair rules out a straight line because gray at `(1,4)` blocks
the direct horizontal route. The output goes down, across, and back up using a
shortest open route. The second and third pairs show that both endpoints are
included and that the result is drawn on a fresh black grid rather than painted
onto the input.

## Hypothesis

Find the two cells of the repeated non-gray color. Starting from the first in
row-major order, perform breadth-first search through black cells and the other
endpoint, exploring neighbors in the order up, down, left, right. Reconstruct
that parent path and paint only it on an all-black output.

The explicit direction order matters if more than one shortest route exists;
the visible examples are consistent with this order. I am using one direct
implementation rather than trying a deliberately wrong alternative.
