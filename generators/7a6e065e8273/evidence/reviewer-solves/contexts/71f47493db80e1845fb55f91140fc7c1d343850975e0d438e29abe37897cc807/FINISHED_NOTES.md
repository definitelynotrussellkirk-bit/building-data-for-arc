# Solve work log

I had no earlier exposure to task `7a6e065e8273`, its rule, generator, private labels,
or prior solution explanations. I used only the public examples produced by the
blind preparation command.

## Revision 1 — orthogonal-neighbour stencil

**Observation.** Every nonzero input cell disappears. Its four orthogonal
neighbours (up, down, left, right) become color 8, clipped to the grid. The
original marker color is irrelevant. Contributions from multiple markers are
unioned: in train example 2, overlaps explain the 21 output cells rather than
24 for six markers.

**Probe.** I checked the listed coordinates manually. For example, the marker at
(2, 2) in train example 0 produces exactly (1, 2), (3, 2), (2, 1), and (2, 3),
and the marker at (1, 3) in train example 1 produces exactly (0, 3), (2, 3),
(1, 2), and (1, 4). The same construction accounts for every visible 8.

**Implementation.** Build a zero grid of the same shape, iterate over every
nonzero cell, and write 8 to each in-bounds orthogonal neighbour. I made the
bounds check row-aware so the function remains safe for a ragged input, although
the visible ARC grids are rectangular.

**Alternatives considered.** A diagonal-X stencil is ruled out directly by the
visible coordinates. Preserving the center or source color is also ruled out;
all source cells are zero in the outputs unless another marker's arm reaches
that coordinate.

**Remaining uncertainty.** No visible marker lies on a boundary. Clipping is the
natural shape-preserving extension and is preferable to wrapping or resizing,
neither of which is suggested by any example.
