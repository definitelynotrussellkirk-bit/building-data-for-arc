# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, prior solve notes, or any assigned-generator source. I used only
the visible challenge and local Python checks.

## Hypothesis

The two complete color-5 columns split each input into three panels. The first
panel demonstrates an incomplete shape, the second panel shows the same shape
after one-dimensional gap filling, and the third panel is the shape to transform.
The output is the third shape cropped to its nonzero bounding box and recolored 8.

The direction is inferred from the demonstration:

- Examples 0 and 2 fill zeros lying horizontally between the leftmost and
  rightmost colored cell of a row.
- Example 1 fills zeros lying vertically between the topmost and bottommost
  colored cell of a column.

I rejected the simpler "fill the whole bounding rectangle" interpretation:
example 0's thin right-hand stem remains thin in the output. I also checked that
the operation is not merely copying the third object: the internal row/column
gap is newly filled in every example.

## Program design

1. Locate the two columns that are entirely color 5.
2. Convert each resulting panel to an occupied/unoccupied mask.
3. Apply horizontal closure and vertical closure separately to panel 1.
4. Select the unique closure that exactly reproduces panel 2.
5. Crop panel 3, apply that closure, and render occupied cells as color 8.

A temporary visible-example regression script was run before implementation; it
failed on the untouched `NotImplementedError`, establishing the red test. The
implemented solver is deliberately strict if the demonstration is ambiguous or
the separator contract is absent, rather than silently guessing.
