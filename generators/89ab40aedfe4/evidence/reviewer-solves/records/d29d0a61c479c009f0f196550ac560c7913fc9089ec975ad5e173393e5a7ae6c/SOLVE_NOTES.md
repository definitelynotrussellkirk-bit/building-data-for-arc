# Solve work log

## Prior exposure

Before this solve I had read only the packet-level instructions and the assigned
visible presentation produced by `python3 review.py blind prepare`. I had not
opened this task's generator, canonical rule, private labels, reference solution,
notes, or audit evidence.

## Revision 1 — stable sort of logical columns by population

The grids have a repeated scaffold. The first row contains a two-cell colored
run for every logical column, with one or more zero separator cells between
runs. In lower rows the first cell of each run remains colored while the second
cell is either colored or zero, so those second cells encode a binary matrix.

I first compared individual row words and considered reversal, cyclic rotation,
and a fixed permutation. Those hypotheses fail because the induced permutation
changes from one training example to another. Comparing whole logical columns
revealed one consistent rule: the output order is the stable ascending order of
the number of colored second cells in each logical column. For example, the five
column populations in training example 0 order as indices 2,1,3,0,4; training
example 1 orders as 3,2,1,4,0, with the tied columns 1 and 4 retaining their
original order. The same rule exactly explains both four-column examples.

The implementation detects the colored-run starts from the fully populated first
row, counts nonzero cells in each run's second column, stably sorts those logical
columns by count, and rewrites only the variable second-cell positions. This
preserves the scaffold and handles both one-zero and two-zero separator widths.

Remaining uncertainty: the visible examples all use one nonzero color and a
fully populated first row, so the solver intentionally relies on those observed
invariants rather than inventing unsupported behavior for other encodings.
