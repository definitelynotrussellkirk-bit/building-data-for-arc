# Visible-only solve notes

## Observation

Every example contains one cell whose color is neither background 0 nor gray 5.
The output preserves all gray cells and the marker. New colored cells appear only
where the input was 0.

For each example, the newly colored cells share both coordinate parities with the
marker:

- example 0 marker `(10,4)` is even-row/even-column, so only even/even zeros fill;
- example 1 marker `(2,9)` is even-row/odd-column, so only even/odd zeros fill;
- example 2 marker `(5,10)` is odd-row/even-column, so only odd/even zeros fill.

Rows or columns matching alone are insufficient, and gray blockers remain gray
even when they occupy the selected parity class.

## Implemented hypothesis

Find the unique non-0/non-5 marker `(mr, mc, color)`. Copy the input, then replace
a cell by `color` exactly when it is 0 and
`(row % 2, col % 2) == (mr % 2, mc % 2)`.
