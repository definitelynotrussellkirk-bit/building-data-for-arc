# Visible-example solve notes

## Initial observations

The transformation is row-local. Empty rows remain empty. A row with exactly two
color-5 cells changes only in the cells strictly between those endpoints: the
interior zeros become color 3, while the endpoint 5s and cells outside the span
stay fixed.

The examples also expose two necessary negative conditions:

- A row with three color-5 cells is unchanged rather than choosing a pair.
- A row with exactly two 5s but nonzero color-4 blockers inside their span is
  unchanged. Therefore the whole interior must initially be zero.

The shortest positive shown is `5,0,5 -> 5,3,5`, so a one-cell interior is legal.

## Proposed rule

For each row independently:

1. Locate all cells of color 5.
2. Continue only when there are exactly two and they are non-adjacent.
3. Continue only when every cell strictly between them is 0.
4. Replace those interior zeros with 3. Leave every other cell unchanged.

## Test-grid predictions

Test 1 fills the spans on rows with endpoint columns `(6,8)`, `(1,3)`, and
`(3,8)`.

Test 2 fills rows with endpoint columns `(3,10)`, `(3,5)`, and `(2,6)`. The row
with color-4 blockers and the row with three 5s remain unchanged.

## Implementation

The solver deep-copies the input, scans rows, checks the exact endpoint count and
all-zero interior, then writes color 3 only into the qualifying interior cells.
