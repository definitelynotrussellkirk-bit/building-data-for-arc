# Blind solve notes

## Hypothesis

The input is split into two equally sized panels by a full-height column of 9s.
The left panel contains a sparse nonzero shape on background 0. The output keeps
values from the right panel exactly at the nonzero coordinates of the left panel,
and writes 0 everywhere else.

## Evidence from visible examples

- Train 0: left-mask coordinates `(1,3)`, `(1,4)`, `(2,3)`, `(2,4)`,
  `(3,3)`, `(3,4)`, `(4,4)` select right-panel values `2,3,2,3,7,8,6`,
  exactly matching the output.
- Train 1 uses mask color 3 rather than 2, so the operation depends on
  non-background occupancy, not on a particular mask color.
- Train 2 again matches coordinatewise masking.

## Implementation

Locate the full-height nonzero separator nearest the center, split the grid into
left and right panels, then return `right[r][c]` where `left[r][c] != 0`, otherwise 0.
