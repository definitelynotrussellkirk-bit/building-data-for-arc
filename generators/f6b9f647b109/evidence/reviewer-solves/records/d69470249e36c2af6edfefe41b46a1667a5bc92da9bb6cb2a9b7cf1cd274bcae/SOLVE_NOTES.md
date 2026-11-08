# Post-repair solve notes

## Exposure declaration

I had already inspected the assigned generator while repairing it, so this is not an independent blind solve. During this solve lane I kept generator code, canonical/Racket source, reference solutions, private labels, and prior solution explanations closed. I used only the visible examples in `solve/README.md` / `challenge.json` and my own coordinate arithmetic.

## Visible pattern

Every input has one red cell (`2`) and one blue cell (`1`). The output preserves both and colors the interior of a shortest king-move/Chebyshev path green (`3`). The path order is not arbitrary:

1. Start at red and take one diagonal step toward blue.
2. Take all excess steps on the dominant axis as one contiguous straight block.
3. Finish with diagonal steps toward blue.
4. Do not recolor either endpoint.

Coordinate checks from the four demonstrations:

- Example 0: red `(0,6)` to blue `(12,3)`, gaps `(12,3)`. Green is the first down-left diagonal `(1,5)`, nine vertical steps through `(10,5)`, then the final interior diagonal `(11,4)`.
- Example 1: red `(9,10)` to blue `(6,0)`, gaps `(3,10)`. Green starts at `(8,9)`, runs left through `(8,2)`, then reaches `(7,1)` before blue.
- Example 2: gaps `(3,2)` give `(3,4)` diagonally, then one vertical step `(4,4)`, then blue.
- Example 3: gaps `(2,3)` give `(7,8)` diagonally, then one horizontal step `(7,9)`, then blue.

These examples distinguish this ordering from all-diagonals-first, all-straights-first, and evenly distributed/Bresenham-style paths.

## Query predictions

- Query 0: red `(8,7)` to blue `(11,5)` gives green at `(9,6)` and `(10,6)`.
- Query 1: red `(12,10)` to blue `(3,4)` gives green at `(11,9)`, `(10,9)`, `(9,9)`, `(8,9)`, `(7,8)`, `(6,7)`, `(5,6)`, `(4,5)`.

## Implementation

`solution.py` locates the endpoints, computes signed row/column directions, uses `abs(row_gap-col_gap)` as the straight-block length, follows the three phases above for `max(row_gap,col_gap)` total moves, and paints only non-endpoint visited cells green.
