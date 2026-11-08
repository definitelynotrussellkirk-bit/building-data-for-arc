# Solve work log

Earlier exposure: none. Before this solve I had read only the packet-level `WELCOME.md`,
`RETURN-GUIDE.md`, and the generated assignment text; I did not open this task's rule,
generator, notes, solutions, audit records, or private labels.

## Revision 1

Observation: every visible input contains exactly one nonzero cell. In each training
output, that cell's color fills its entire row and its entire column, forming a cross
that reaches all four grid boundaries. This accounts for all changed cells in all three
examples, including corner/edge markers and rectangular grids.

Hypothesis: locate the single nonzero cell `(r, c, color)`, copy the grid, fill row `r`
and column `c` with `color`, and leave all other cells unchanged. I first ran a local
training-pair assertion against the untouched template and observed the expected
`NotImplementedError`; after implementing the hypothesis, I reran the same assertions.

Alternatives considered: rays extending only away from the nearest border, or filling
only border-facing directions. The corner examples do not distinguish some ray
formulations, but the first example has the marker on the left edge and requires both
upward and downward vertical extension, while all examples are exactly explained by
full row-plus-column fill. Remaining uncertainty is limited to malformed inputs with
zero or multiple nonzero cells; the visible task consistently presents one marker.
