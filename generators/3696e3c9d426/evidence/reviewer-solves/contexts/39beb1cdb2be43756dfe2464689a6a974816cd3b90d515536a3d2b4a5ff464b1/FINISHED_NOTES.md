# Solve work log

## Exposure before the solve

I had not opened task `3696e3c9d426`'s generator, rule, notes, reference
solution, private labels, or any earlier solution explanation. Before the blind
preparation I had read the packet's general `WELCOME.md`, `RETURN-GUIDE.md`, and
`ARC-DESIGN.md`; those did not contain this task's transformation or examples.

## Revision 1 — independent downward gravity by column

**Observation.** Input and output dimensions and color counts are unchanged.
For each column, the output contains the same nonzero colors packed against the
bottom. Their original top-to-bottom order is preserved. For example, train 0
column 2 changes from `[0,5,3,0,8,0,0,0]` to `[0,0,0,0,0,5,3,8]`, while column
5 changes from `[7,0,0,0,0,0,1,0]` to `[0,0,0,0,0,0,7,1]`.

**Hypothesis.** Treat 0 as empty space and apply gravity downward independently
to every column. Nonzero cells keep their colors, columns, and relative vertical
order.

**Probe.** I manually checked every occupied column in all three visible training
pairs. The rule accounts for isolated cells, two-cell stacks, three-cell stacks,
and columns already containing low cells. No horizontal motion, sorting by
color, or interaction between columns is needed.

**Implementation.** For each column, collect its nonzero values from top to
bottom and write them into the bottommost rows of a zero-filled output grid.

**Alternatives considered.** Moving each connected component to the floor gives
the same result on singleton-only examples, but the visible evidence is more
directly expressed as stable per-column compaction. Sorting colors or moving all
cells as one global object contradicts the preserved order and independent
landing heights.

**Remaining uncertainty.** The examples contain only singleton colored cells,
so they do not distinguish independent-cell gravity from rigid-object behavior
for multi-cell objects. The submitted rule is the simplest operation supported
by every visible pair.
