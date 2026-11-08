# Visible-only solve notes

## Observation

All three training inputs contain one contiguous horizontal band of nonzero rows in an otherwise zero grid. The output keeps the width, height, colors, and row contents, but fills every row by periodically repeating that source band.

The phase is tied to the source location, not reset at output row 0:

- Example 0 has source rows 9–10 (`sparse, full`). Keeping row 9 as `sparse` forces output row 0 to be `full`.
- Example 1 has source rows 3–5 (`sparse, full, sparse`), repeated with row 3 unchanged.
- Example 2 has source rows 1–4. Output row 0 is the cyclic predecessor of source row 1, while source rows 1–4 remain exactly in place.

## Hypothesis

1. Find the first and last rows containing any nonzero cell.
2. Treat that inclusive contiguous row band as the repeating motif.
3. For every output row `r`, copy motif row `(r - source_start) mod motif_height`.
4. Preserve each copied row exactly; there is no horizontal transformation.

This predicts query 0 as a three-row motif anchored at row 5 and query 1 as a two-row motif anchored at row 9.

## Implementation choice and limits

The visible tasks use 0 as background, so occupancy is `any(cell != 0)`. The implementation returns an unchanged copy for an all-zero grid. It deliberately does not infer a different background color or split separated occupied bands because neither behavior is supported by the visible examples.
