# Solve work log

I had not seen task `5a215cef8bd1`'s generator, Racket rule, reference solution,
private labels, or earlier solution explanation before this solve. I had read only
the packet-level workflow/design documents and the visible examples prepared here.

## Revision 1 — four marker-selected orientations

The nonzero input decomposes into one blue motif (color 2) and four singleton
markers (colors 1, 3, 4, 6) at the corners of a rectangle. The output is a 2×2
mosaic separated by one all-zero row and column. Cropping the blue motif to its
bounding box and comparing quadrants across all three demonstrations gives a
consistent marker dictionary:

- 1: identity
- 3: rotate 90° clockwise
- 4: rotate 180°
- 6: reflect left-to-right

Each marker's location chooses the corresponding output quadrant, and motif cells
are recolored from 2 to 7. I checked the mapping manually on the asymmetric 3×3,
2×2, and 4×4 motifs; every displayed training quadrant matches. The implementation
therefore extracts the motif, finds the two marker rows and columns, transforms a
copy for each corner, and joins the four tiles with a zero cross.

Remaining uncertainty: the visible motifs are square, which makes all four
orientations tile-compatible. The program rejects a non-square case whose
90-degree rotation would not fit the same 2×2 layout rather than guessing a
padding convention unsupported by the examples.
