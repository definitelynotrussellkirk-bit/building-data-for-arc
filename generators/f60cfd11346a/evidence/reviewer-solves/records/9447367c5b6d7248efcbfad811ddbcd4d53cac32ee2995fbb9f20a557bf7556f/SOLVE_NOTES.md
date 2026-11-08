# Solve work log

## Prior exposure

Before this solve I had already inspected the task's generator and selected Racket authority while repairing the generator, so earlier rule exposure is **yes**. I did **not** consult either source during this solve revision; I used only the freshly prepared `challenge.json` / rendered visible examples. I did not consult private query labels or a reference solution.

## Revision 1

**Visible pattern.** Every demonstration preserves all nonzero cells. The blue `2` is a seed. Exactly the zero-valued cells reachable from that seed by four-neighbor moves through zero cells turn azure `8`; gray `5` and the colored `1`/`9` cells are barriers. Diagonal contact does not connect regions.

The branch walls are important: in training example 1, only the lower-left pocket connected to `2` fills, while the larger zero area above the partial horizontal wall stays unchanged. In training examples 0 and 2, the colored cell beside `2` blocks crossing and only the small zero component on the other side of the seed fills. This rules out simply filling an entire geometric half or quadrant.

**Program.** Copy the grid, start a breadth-first search at every `2`, traverse only orthogonally adjacent `0` cells, recolor each reached zero to `8`, and leave all other cells unchanged.

**Alternatives considered.** Filling the row/column around `2`, filling a coarse quadrant, or treating colors `1`/`9` as passable all contradict visible demonstrations. Remaining uncertainty is low: the three examples explicitly exercise both colored blockers and an internal branch that separates same-side zeros.
