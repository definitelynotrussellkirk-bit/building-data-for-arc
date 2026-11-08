# Solve work log

I had earlier exposure to the assigned generator's intended rule while doing the
required repair review. After `review.py solve prepare`, I did not consult the
generator, Racket source, reference outputs, private labels, or prior solution
explanations. This attempt was reconstructed from the visible examples.

## Revision 1 — count empty rows inside the gray U

Each input contains a gray (`5`) upright U-shaped container. I used the bounding
rows and columns of the gray cells to identify its interior. The floor row is
excluded. Among the rows from the top of the side walls down to just above the
floor, a row counts only when every cell strictly between the two side walls is
zero; even one cyan (`8`) cell makes that row nonempty.

The output is always 3×3. It contains as many cyan cells as the empty-row count,
painted as a clockwise spiral prefix starting at the top-left: across the top,
down the right, across the bottom from right to left, up the left, then center.
Counts of nine or more naturally saturate because the spiral has nine cells.

Visible checks:

- Example 0 has two wholly empty interior rows, producing the first two spiral
  cells.
- Example 1 has seven empty rows despite cyan in both the first and last
  interior rows, producing a seven-cell prefix.
- Example 2 has nine empty rows and therefore a solid cyan 3×3 output.
- Example 3 has six empty rows; partial cyan rows do not count, matching the
  shown six-cell clockwise prefix.

For the two hidden queries, the visible inputs imply counts two and six,
respectively. The implementation follows the same container-relative test and
never relies on a fixed position or width.
