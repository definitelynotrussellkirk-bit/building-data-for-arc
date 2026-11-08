# Blind solve notes

Human visible-only work log. I did not inspect any generator, canonical rule,
reference solution, private label, notes, or audit evidence.

## Revision 1

Each visible input contains exactly two yellow (`4`) cells. The output removes
both and places one azure (`8`) cell at their coordinate midpoint:

- `(2,7)` and `(8,1)` -> `(5,4)`
- `(0,0)` and `(0,2)` -> `(0,1)`
- `(4,1)` and `(12,9)` -> `(8,5)`

Thus the two queries should place the output marker at `(3,4)` and `(2,2)`.
The implementation finds the two nonzero cells, requires an integral midpoint,
and emits a same-size zero grid with an `8` at that midpoint.
