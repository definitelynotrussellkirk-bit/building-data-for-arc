# Blind solve notes — f59691ac00f3

## Initial observations

- Color 7 is the background. Only the supplied top row contains the seed pattern.
- In the first example, two 5 cells two columns apart create a 2 at their midpoint one row below.
- In the second example, the active positions alternate parity by row and shrink inward. Reading only active cells, each next value is the 2/5 complement of the upper-left value from the pair that brackets it.
- The third example resolves the spacing ambiguity: a next-row cell is created from two non-background cells at columns `c-1` and `c+1`, even when the source row is contiguous. This shrinks a contiguous run by two cells per row.

## Hypothesis

For every row below the first, start with background 7. At column `c`, if the previous row has non-background cells at both `c-1` and `c+1`, write the complement of the upper-left cell (`2 -> 5`, `5 -> 2`); otherwise leave 7. Repeat downward to the available grid height.

## Predictions

- Test 1 should form a six-row inward triangle: 5s at even columns, then 2s at odd columns, alternating and shrinking by one active point per row.
- Test 2 should produce two 2s at columns 4 and 6 on row 1, one 5 at column 5 on row 2, then background-only rows.
