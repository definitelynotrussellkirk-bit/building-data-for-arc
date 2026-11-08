# Solve notes

This is a human-authored visible-example work log. I had earlier exposure to the task family during generator review, so this is not a blind solve; I did not consult the generator, Racket rule, prior solution, or private labels during this episode.

## Hypothesis from the visible examples

The 11x11 input is a 3x3 meta-grid of 3x3 tiles separated by color-6 lines. A symbol is a four-cell diamond. Examples 0–2 each contain a color-5 or color-8 diamond in addition to the two color-2 diamonds, and all three map to a 16x16 all-color-7 rejection grid. Therefore any non-2 symbol is contamination.

Examples 3–4 contain only two color-2 diamonds and preserve the 11x11 frame. Their relative placement completes a small oriented motif with proposed color-8 and color-5 diamonds. Example 4, with 2s at meta-cells (0,0) and (1,1), adds 8 at (1,2) and 5 at (2,1). Example 3, with 2s at (1,2) and (2,1), proposes 8 at (2,0); the other proposal falls below the 3x3 meta-grid and is omitted. This supports clipping rather than wrapping.

I encoded the four geometric cases (same column, same row, descending diagonal, ascending diagonal), retained observed symbols when a proposal collides, and clipped proposals outside meta-grid coordinates 0..2. Query 0 should add a color-8 diamond at meta-cell (2,2); query 1 contains both contaminating colors and should reject to 16x16 color 7.
