# Solve notes — 994f16f93144

## Visible-only evidence

- Outputs preserve dimensions and all cells except selected nonzero centers, which become cyan (`8`).
- Training pair 1 shows both diagonal slopes: the middle of each same-color diagonal triple changes, while endpoints do not.
- Training pair 2 contains a four-cell diagonal run of color 4. Its two interior cells both become cyan, which rules out “only isolated three-cell components” and implies overlapping local three-cell windows.
- Training pair 3 contains longer color-2 diagonal runs; every interior cell with equal opposite diagonal neighbors changes, while isolated, vertical, and mismatched structures remain unchanged.

## Hypothesis

For each interior nonzero cell, compare it with the two opposite neighbors on each diagonal. Change the center to `8` when either opposite pair has the same color as the center. Evaluate against the original input so overlapping windows are all recognized.

## Implementation

Copy the grid, scan interior coordinates, test both diagonal predicates against the input, and write cyan into the copy. This preserves endpoints and unrelated motifs.
