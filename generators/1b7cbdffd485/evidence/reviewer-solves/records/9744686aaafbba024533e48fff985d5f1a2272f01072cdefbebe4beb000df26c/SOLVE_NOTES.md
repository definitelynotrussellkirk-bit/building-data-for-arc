# Solve work log

I had not seen task `1b7cbdffd485`, its generator, its Racket rule, private
labels, or earlier solution notes before this blind solve. I used only the
visible grids printed by `review.py blind prepare` and calculations over
`challenge.json`.

## Revision 1 — spatial color-region compression

### Observations

- Train 0 has three broad, noisy horizontal regions: 9 above 8 above 7. Its
  output is the vertical sequence `[[9], [8], [7]]`.
- Trains 1 and 2 have broad, noisy vertical regions. Their outputs are the
  corresponding left-to-right color sequences, as one-row grids.
- The exact color counts and jagged boundaries vary, so sorting by count or by
  numeric color value does not explain the outputs.

### Probe

Using a small Python calculation on the visible grids, I computed each color's
mean `(row, column)` position. In Train 0 the centroid row span was about 11.09
versus column span 1.28. In Trains 1 and 2 the column spans were about 8.60 and
10.09, while row spans were below 0.41. Sorting centroids along the larger span
reproduces all three outputs and also tolerates the noisy boundaries.

### Program

The solver collects every cell of each color, computes the color centroids,
chooses vertical output when centroid row span is strictly larger than column
span, and otherwise chooses horizontal output. It sorts colors from top to
bottom or left to right along that axis. The strict comparison intentionally
makes a diagonal/tied case horizontal.

### Queries and uncertainty

- Query 0 has a clear left-to-right centroid ordering, predicting
  `[4, 5, 3, 2]`.
- Query 1 contains a large 6 region and an 8 square in the lower-right corner.
  The two centroid spans tie exactly, so the examples do not uniquely determine
  whether a diagonal two-color case should be returned as a row or column. I
  use a row as the deterministic default; either orientation would preserve the
  color order `6, 8`, but output shape is still a genuine uncertainty.
- A different plausible implementation could infer an axis from border contact
  or a principal component. For the visible examples those agree with the
  centroid-span rule except for the diagonal tie, where no training example
  provides a decisive convention.
