# Solve work log

I had not opened task `33275a4aae3e`'s generator, rule, reference solution,
private labels, prior notes, or audit material before this solve. I had only read
the packet's general instructions and the assignment text naming the task.

## Revision 1 — rectangular interior/exterior coloring

**Visible pattern.** Each input uses background 0 and one line color. The output
preserves every line-colored cell, turns most background cells to 3, and turns a
single rectangular interior to 2. Internal foreground segments remain unchanged.

**Boundary hypothesis.** Long vertical construction lines can be separated from
short vertical-looking stubs by their contiguous run length. In all three visible
examples, the outermost columns whose longest foreground run is at least half the
grid height are the left and right sides of the colored rectangle. Horizontal
rectangle sides are then the topmost and bottommost rows whose foreground segment
covers every column from the left boundary through the right boundary.

**Probe.** A challenge-only Python scan measured maximal contiguous runs. The
candidate vertical columns were:

- example 1: 5, 9, 15, 20 (plus column 12 only as a short run, excluded);
- example 2: 4, 14 (the short column-8 fragments are excluded);
- example 3: 6, 15.

Using the outermost candidates yields visible rectangles `(rows 3..14,
columns 5..20)`, `(4..16, 4..14)`, and `(3..13, 6..15)`, exactly matching the
2-colored regions. The remaining 0 cells become 3.

**Alternatives considered.** Selecting the two longest columns fails on example
1 because internal column 9 is longer than the true left boundary. Selecting the
longest horizontal rows alone is also insufficient because an internal row can
be just as long as a boundary. The paired construction above uses both axes.

**Remaining uncertainty.** The half-height threshold is inferred from the visible
family rather than proved from an exposed specification. It cleanly separates all
visible long construction lines and decorative stubs, and the tests show the same
layout signature.
