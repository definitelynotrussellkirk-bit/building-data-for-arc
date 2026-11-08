# Solve work log

Earlier exposure: **yes**. Before this visible-only episode I had already reviewed the assigned generator and authority while repairing it. During this episode I used only `solve/README.md` / the visible examples; I did not reopen generator code, the Racket rule, reference solutions, private labels, or prior solution explanations.

## Revision 1 — quadrant-normalized motif mosaic

The examples preserve every nonzero connected motif but remove its absolute translation. Each motif is tightly cropped, then assigned to one of four output slots by whether its centroid lies above/below and left/right of the input center. The output is a 2×2 mosaic in the same TL/TR/BL/BR arrangement, with one all-zero gutter row and one gutter column. Each mosaic row/column is sized to the largest crop in its two slots; an absent slot contributes a minimum size of one cell, explaining the blank quadrants in examples 0–3.

I implemented same-color 4-connected component extraction, centroid quadrant classification using integer arithmetic, tight cropping, and sparse pasting into the normalized mosaic. The visible examples also support keeping only the first component in a quadrant if an unexpected duplicate appears, though the visible generator instances have at most one.

Remaining uncertainty: the examples do not establish behavior for a component whose centroid lies exactly on the geometric centerline, or for multiple motifs in one quadrant. Those cases are outside the visible support; the implementation uses bottom/right for equality and first-in-row-major order for a duplicate slot.
