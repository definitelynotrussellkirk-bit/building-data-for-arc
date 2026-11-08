# Solve work log

## Prior exposure

Before this blind solve I had read only the packet-level workflow documents and the assignment text. I did **not** open this task's generator, Racket rule, canonical/private answers, reference solution, audit records, or prior solution notes.

## Revision 1 — parity lattice anchored by the unique colored marker

**Observation.** Each training input contains gray cells (`5`), black cells (`0`), and exactly one cell of another color. The output preserves every gray cell and existing marker cell. It changes only some black cells to the marker color.

**Hypothesis.** Let the marker be at `(r0, c0)`. Recolor a black cell `(r, c)` exactly when `r % 2 == r0 % 2` and `c % 2 == c0 % 2`. This is a spacing-two rectangular lattice, not an ordinary checkerboard based only on `(r+c) % 2`.

**Visible probes.** In training example 0, the marker is at `(6,2)`, so both coordinates are even; recolored cells occur only at even rows and even columns. Example 1 has marker `(8,5)`, giving even rows and odd columns. Example 2 has marker `(9,10)`, giving odd rows and even columns. These three examples independently exercise three of the four parity combinations and agree with the same rule. Gray cells interrupt the lattice and are never overwritten.

**Implementation.** Find the sole value outside `{0,5}`, retain its coordinate and color, deep-copy the grid through a comprehension, and recolor only zero cells matching both coordinate parities. The implementation rejects nonrectangular grids or inputs without exactly one marker rather than silently selecting an arbitrary marker.

**Alternatives considered.** A checkerboard rule based on equal `(row + column) % 2` is contradicted by example 0 because it would also color odd-row/odd-column zeros. A rule based on the marker's row alone or column alone is likewise contradicted by unchanged zeros in the other coordinate parity.

**Remaining uncertainty.** The unseen queries could theoretically introduce multiple marker cells, but all visible examples and queries contain exactly one. The intended visible pattern is therefore strongly identified.
