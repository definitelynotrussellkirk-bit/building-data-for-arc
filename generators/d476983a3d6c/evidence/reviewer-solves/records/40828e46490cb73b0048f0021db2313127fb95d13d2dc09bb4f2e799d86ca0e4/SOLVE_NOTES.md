# Solve notes

This is a human work log from the visible examples in `solve/README.md`.
I had earlier rule exposure during the generator repair, so this is not a blind solve; I did not reopen the generator, Racket rule, reference labels, or prior solution text during this solve phase.

## Hypothesis

- The top-left cell is a command and remains unchanged.
- Ignore that cell when listing other nonzero colors in row-major first-appearance order.
- A color appearing exactly twice defines two endpoints. Start from the row-major first endpoint.
- Command `1`: paint the horizontal segment from the first endpoint to the second endpoint's column, then the vertical segment to the second endpoint.
- Command `2`: paint the vertical segment from the first endpoint to the second endpoint's row, then the horizontal segment to the second endpoint.
- Begin from a copy of the input, so singleton colors remain unchanged.
- Process colors sequentially, so later colors overwrite earlier ones at overlaps.

## Visible checks

Train 0 shows command 1, including an aligned pair and overlapping paths. Train 1 shows command 2. Train 2 confirms a singleton (`9`) remains unchanged. Train 3 confirms command 2 with three paired colors plus a singleton (`6`).

The implementation applies this rule generically to both query grids.
