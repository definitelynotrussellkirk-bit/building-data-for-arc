# Solve work log

## Exposure statement

This is the required post-repair solve, not a blind solve. Before `solve prepare`
I had already reviewed the selected generator and canonical rule, so earlier rule
exposure is **yes**. After preparation I did not reopen the generator, Racket
source, reference solutions, private labels, or previous solution explanations.
The implementation below was checked only against the ten visible pairs and the
official visible-only checker.

## Visible hypothesis

Every input contains only background `0` and cyan `8`; spatial arrangement and
input dimensions vary while equal cyan counts produce the same 5×5 output.
Counting cyan cells explains all visible classes:

- counts 5 and 7 produce a one-cell 2×2 glyph;
- counts 8 and 10 produce a two-cell glyph;
- counts 13, 14, and 15 produce a three-cell glyph;
- count 17 produces a four-cell glyph.

Thus the glyph size is `floor(number_of_8s / 4)`. The 2×2 fill order visible in
the examples is bottom-right, bottom-left, top-right, top-left. The same tile is
copied into the four corners of a 5×5 output, leaving row 2 and column 2 zero.
Input geometry is deliberately ignored.

The untouched template first raised the expected `NotImplementedError`. I then
implemented only this count-and-repeat rule and checked all ten visible examples.

## Query deductions

- Query 0 contains 17 cyan cells, so `17 // 4 = 4`: all four cells of every
  corner tile are cyan.
- Query 1 contains 14 cyan cells, so `14 // 4 = 3`: each corner tile contains
  bottom-right, bottom-left, and top-right cyan cells.

Remaining uncertainty is only outside the demonstrated count range. The prepared
queries lie inside it, and the implementation clamps the tile size to 0–4 rather
than indexing beyond the four visible positions.

## Visible-only check result

Official revision 1 completed with 10/10 visible examples passing. I stopped
because one compact rule explains every visible count class and both queries;
no additional revision or deliberately wrong negative was needed.
