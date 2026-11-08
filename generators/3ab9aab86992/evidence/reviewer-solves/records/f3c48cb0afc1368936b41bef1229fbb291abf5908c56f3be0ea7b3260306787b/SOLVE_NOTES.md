# Post-repair solve notes

This is a human work log from the visible examples only. I had earlier rule
exposure from reviewing the assigned generator, so this is intentionally recorded
as an exposed post-repair solve rather than a blind solve.

Hypothesis: the most frequent color is background. Every non-background
four-connected component is a three-cell L inside a 2×2 box. The L's occupied
elbow determines one of the four output corners, independently of its input
position or color. Replace the input with a background grid and draw an enlarged
border L in that corner. For side length `n`, each arm contains `(n-1)/2` cells
including the corner. Repeated colors can form separate components and therefore
can select multiple corners.

The three visible examples support all four orientations, repeated colors, and
background color 0 as an ordinary object color when another color is the
majority background. The implementation therefore extracts same-color
four-connected components rather than grouping all cells by color.
