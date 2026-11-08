# Solve work log

## Prior exposure

I had not opened task `ad4e2cd6e3bc`'s generator, reference rule, notes,
solutions, private labels, or audit records before this solve. I only read the
packet-level assignment instructions and `solve-blind/challenge.json`.

## Revision 1 — connected-component flood fill

**Observation.** In every training pair, color 2 stays fixed. Some or all color-0
cells become color 8, while color 5 is unchanged. In the first pair, the two
isolated 0 cells not connected to the 2 remain 0. The cells changed to 8 are
exactly the 4-neighbor-connected component of 0 cells that touches the 2.
The other examples have one large connected 0 region, so all their 0 cells are
recolored.

**Hypothesis.** Treat the 2 as a seed. Flood through orthogonally adjacent 0
cells only, recoloring each reached 0 to 8. Preserve the 2, all 5 cells, and any
0 component separated by 5 barriers. Diagonal contact alone should not connect
regions.

**Probe.** I first ran a visible-example harness against the supplied stub and
observed the expected `NotImplementedError`, establishing that the harness would
catch a missing implementation. I then implemented a breadth-first flood fill
from every 2 seed on a copied grid and planned to compare all three visible
training outputs exactly.

**Alternatives rejected.** "Recolor every 0" fails the first training pair.
Row/column ray filling also fails because the marked component can bend through
multiple rows and columns. Eight-neighbor connectivity is unsupported and could
incorrectly cross diagonal corners.

**Remaining uncertainty.** The examples show one 2 marker; the implementation
handles multiple markers by filling the union of their zero components. Empty
or marker-free grids are returned unchanged.
