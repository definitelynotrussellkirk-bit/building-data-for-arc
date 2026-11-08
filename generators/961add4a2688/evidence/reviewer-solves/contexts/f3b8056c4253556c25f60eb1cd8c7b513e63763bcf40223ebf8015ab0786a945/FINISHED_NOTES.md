# Visible-only solve notes

This is a human work log based only on the prepared visible examples.

Hypothesis: color 8 forms a rectangular frame. Preserve that frame and erase all other cells outside it. Within each interior column independently, remove the zero gaps and move the nonzero colored cells to the top of the frame, preserving their original top-to-bottom order. Columns do not exchange markers.

Evidence: examples 0 and 3 contain multiple markers in the same columns, which rules out global row packing and shows that vertical order is preserved rather than sorting by color. Example 2 shows a column that is already tightly packed and remains unchanged while another column closes its gap.

Implementation: derive the color-8 bounding rectangle, redraw its border on a zero canvas, then scan each interior column top to bottom and emit its nonzero values starting at the first interior row.
