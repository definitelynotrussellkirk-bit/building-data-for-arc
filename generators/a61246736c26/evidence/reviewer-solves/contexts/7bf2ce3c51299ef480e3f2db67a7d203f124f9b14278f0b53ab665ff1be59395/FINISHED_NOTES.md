# Solve work log

## Exposure before solving

Before this blind solve I read only packet-level handoff material (`START-HERE.md`,
`WELCOME.md`, `AGENTS.md`) and, inadvertently, the general `ARC-DESIGN.md` overview.
I did **not** open task `a61246736c26`'s generator, Racket rule, canonical entry,
reference solution, private query labels, notes, or audit evidence. I also had not
opened the assigned repair generator.

## Revision 1 — baseline checker probe

The supplied `solution.py` raised `NotImplementedError`. I deliberately ran the
visible-only checker first to establish that the harness rejected the missing
implementation. It reported an execution error and 0/3 visible examples passed.

## Revision 2 — repeated-mask plus swatch composition

### Observation and hypothesis

The input is divided into three six-row bands, labelled at the far left, and three
or four six-column tile positions. In each tile column:

* two bands contain exactly the same sparse 4×4 mask, drawn with color 2 on color 8;
* the third band contains a solid 4×4 swatch in another color;
* the swatch-bearing band's left label becomes the output tile's border;
* the repeated mask is recolored with the swatch color;
* output tiles remain in input column order, separated by color 8.

For example, in train example 0's first tile column, bands labelled 5 and 0 share
the same sparse mask while band 9 has a solid color-7 swatch. The first output tile
therefore has a color-9 frame and the shared mask painted color 7. The other tile
columns follow the same relation, and all three training examples agree.

### Implementation

The solver detects non-separator row bands, iterates tile starts `1, 8, 15, ...`,
finds the unique solid interior, checks that the other two interiors match, and
builds the framed/recolored 6×6 result tile. It raises a clear error if the expected
visible structure is absent rather than silently guessing.

### Remaining uncertainty

The solution assumes the demonstrated layout: full separator rows, six-row bands,
six-column tiles at a seven-column stride, one solid swatch per tile column, and two
identical sparse masks. Those assumptions are supported by every visible example.
