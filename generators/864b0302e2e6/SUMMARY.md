# 864b0302e2e6

An odd square 0-background grid has size `2*q+1`, with `q` normally 4–6.
The all-zero center row and column split four equal `q×q` quadrants. Three
quadrants contain the same randomly sampled, nonempty proper subset of local
quadrant cells, painted in one shared nonzero color. The fourth quadrant is
empty. Fill that missing quadrant with the same motif at the same local
coordinates and color, completing the four-way repetition.

`missing_quad=0..3` is an exact visible control in row-major order: top-left,
top-right, bottom-left, bottom-right. The motif is not the archival fixed
four-cell `MOTIF`; that constant is retained only for explicit degenerate
fixtures.

Kind: `per_puzzle`. Imported version: `2.1.2`.
Approval is derived by the catalog from current code and retained evidence.
