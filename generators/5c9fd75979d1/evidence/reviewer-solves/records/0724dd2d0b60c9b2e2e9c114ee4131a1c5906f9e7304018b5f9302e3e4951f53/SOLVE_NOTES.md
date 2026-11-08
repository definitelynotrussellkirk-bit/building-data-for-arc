# Blind solve work log

The input is a matrix of large, mostly solid colored tiles with occasional zero holes.
The output replaces each tile by one cell of its color and reverses the tile columns.

Evidence:
- Example 1 has tile rows `[1,4,6]` and `[9,2,7]`; output is `[6,4,1]`, `[7,2,9]`.
- Example 2 similarly maps `[3,6,4]`, `[8,7,5]` to their horizontal reversals.
- Example 0 demonstrates that adjacent slots can have the same color (`6,6`), so connected components alone are insufficient.

Implementation:
1. Split nonzero rows into horizontal tile bands.
2. For every active input column, compute the modal nonzero color in each band.
3. Treat a change in the tuple of per-band column modes as a shared tile-column boundary.
   This lets another band reveal a boundary hidden by equal adjacent colors in one band.
4. Take the modal nonzero color in each band/slot and reverse the slot order.

Predicted masked outputs:
- Query 0: `[[5,1,3],[8,8,1],[3,6,9]]`.
- Query 1: `[[3,2],[4,8]]`.
