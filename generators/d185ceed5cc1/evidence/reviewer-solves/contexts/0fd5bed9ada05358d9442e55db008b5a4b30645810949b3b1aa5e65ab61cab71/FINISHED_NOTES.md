# Visible-only solve notes — d185ceed5cc1

## Hypothesis

Color `8` cells are fixed walls. Each row is split independently into maximal
contiguous segments that do not contain an `8`, including segments at the left
or right grid edge. Within each segment, discard the zeros, preserve the
remaining colors' left-to-right order, and right-align those colors inside the
same segment. Rows do not interact.

## Evidence from the visible examples

- Example 0 row 0 splits as `[6,0] | 8 | 8 | 8 | [7,5,0] | 8 | [0,0,2]`;
  the nontrivial segments become `[0,6]`, `[0,7,5]`, and `[0,0,2]`.
- Example 1 has open edge segments and row-dependent wall positions, ruling out
  a fixed vertical-chamber interpretation.
- Example 2 preserves color order: row 0's `9,5,1` becomes right-aligned as
  `0,0,0,9,5,1`, not sorted or reversed.

The implementation scans each row, copies every wall in place, and rebuilds
one non-wall segment at a time. It does not mutate the input.

## Exposure declaration

I had earlier exposure to the task rule while reviewing the assigned generator.
During this solve episode I used only the prepared visible examples and did not
consult the Racket source, generator source, private labels, or prior reference
solutions.
