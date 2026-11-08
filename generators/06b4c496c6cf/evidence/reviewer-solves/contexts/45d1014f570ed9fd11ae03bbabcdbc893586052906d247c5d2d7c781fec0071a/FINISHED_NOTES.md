# Solve work log

This is the required post-repair visible-only solve. I had already inspected the assigned generator and canonical rule during the repair phase, so earlier rule exposure is **yes**. During this solve episode I did not reopen the generator, Racket source, reference solution, or private labels; I used the eight visible examples printed by `review.py solve prepare`.

## Revision 1 — bbox-normalized template stamping

The color-2 cells form a reusable shape. For each cell whose color is 3 through 9, the output places a copy of that shape with its bounding-box top-left aligned to the marker and fills the copy with the marker's color. The output starts blank, so the source color-2 object disappears.

Visible evidence:

- Example 0 copies the same five-cell shape at markers 9, 7, and 4.
- Example 1 has a template whose bounding-box top-left is empty. The copies preserve that empty corner, showing that the marker denotes the bounding-box corner rather than an occupied template cell.
- Example 3 repeats color 3 at two anchors and produces both copies.
- Examples 2, 4, 5, and 6 show clipping at boundaries and overlaps; the larger color survives a cross-color overlap, consistent with applying colors in ascending numeric order.
- Example 7 shows two markers of the same color both generate copies.

The implementation extracts all color-2 offsets relative to the minimum template row and column, iterates colors 3..9, stamps at every marker, clips out-of-bounds cells, and returns the blank-based result.

Remaining uncertainty before checking: only the tie order between markers of the same color is unobservable, but it cannot affect the result because they write the same value.
