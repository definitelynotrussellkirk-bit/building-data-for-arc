# Solve work log

## Exposure declaration before work

I had not opened task `3696e3c9d426`'s generator, Racket rule, notes, reference
solutions, private labels, or previous solve explanations. Before this blind solve
I had only read the packet-level instructions and assignment text.

## Revision 1 — independent column gravity

Visible examples are sparse rectangular grids with `0` as background. Comparing
input and output coordinates showed that every colored cell stays in its original
column, while each column's nonzero sequence is packed against the bottom edge.
The top-to-bottom order is preserved. For example, training example 0 column 3
contains `8,5,1` and becomes rows 4–6 as `8,5,1`; column 5 contains `4,6` and
becomes rows 5–6 as `4,6`. The same rule accounts for all occupied columns in all
three training pairs, including different 6×6 and 7×7 sizes.

Implemented `solve(grid)` by collecting nonzero values independently per column
and writing them to the bottom of an all-zero output. Alternatives rejected:
whole-grid translation fails because columns have different lowest occupied rows;
row-wise compaction fails because colors never change columns; sorting colors
fails because observed order is stable and not numeric.

Remaining uncertainty: none within the visible support. The inferred rule assumes
`0` is always background and gravity acts downward rather than toward a marker;
all examples support that interpretation.
