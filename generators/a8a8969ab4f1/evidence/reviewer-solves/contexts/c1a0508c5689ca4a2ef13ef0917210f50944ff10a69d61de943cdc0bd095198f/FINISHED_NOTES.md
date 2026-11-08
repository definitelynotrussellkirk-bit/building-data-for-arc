# Visible-only solve notes

## Observations

- Output dimensions and all zeros are preserved.
- In each row whose first cell is a nonzero color, every `8` later in that row
  becomes that first-cell color. Different rows use different colors independently.
- The second and third training pairs contain `8` cells in rows whose first cell
  is `0`; those cells stay `8`. This rejects a tempting rule that erases or
  borrows a neighboring row's key for unkeyed rows.
- The first-column key itself is unchanged.

## Hypothesis

For each row, read column zero as its key. If the key is nonzero, replace every
`8` in columns one onward with that key. If the key is zero, leave the entire row
unchanged. Preserve all other cells.

This hypothesis accounts for every changed and unchanged cyan cell in all three
visible examples, so I am testing it directly without an exploratory wrong
revision.
