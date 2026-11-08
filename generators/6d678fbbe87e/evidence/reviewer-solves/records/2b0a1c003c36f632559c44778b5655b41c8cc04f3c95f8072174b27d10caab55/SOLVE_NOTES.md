# Solve notes

## Visible-example hypothesis

Each output preserves the input shape and all existing cells. For every 2×2
window in the input that contains three copies of one non-zero color and one
zero, the zero is filled with that color.

The examples imply a local scan rather than a whole-object rule: training
example 1 has a connected color-1 shape with two qualifying 2×2 windows, and
both holes are filled. The scan must be simultaneous against the original
input, because newly filled cells should not recursively create further fills.

## Implementation

Copy the grid, inspect every original 2×2 window, and write each qualifying
missing corner into the copy. No Racket rule or private answer was consulted
while writing this solve episode. Earlier rule exposure occurred during the
required generator repair, so this is an exposed visible-only solve, not blind.
