# Solve work log

Earlier exposure before this blind episode: none to this task's rule, generator,
notes, solutions, labels, or audits. I opened only the packet-wide instructions,
the assignment text, and `solve-blind/challenge.json` before writing this solution.

## Revision 1 — shortest-path union

**Observation.** Each example contains a gray (`5`) barrier system, one red (`2`)
cell, and one green (`3`) cell. The output preserves all non-background cells and
turns selected black (`0`) cells azure (`8`). In the first example both equal
routes around the central gray block are colored. In the third example the two
routes around the block are colored, but the downward dead-end spur is not.

**Hypothesis.** Treat every cell except gray `5` as traversable in the 4-neighbor
grid. Color exactly those black cells that belong to at least one shortest path
between `2` and `3`. A cell is on such a path precisely when its distance from
`2` plus its distance from `3` equals the endpoint distance.

**Probe.** I computed two breadth-first-search distance maps from the visible
training inputs and compared the predicted grids with all three visible outputs.
All three matched exactly: shortest-path lengths 10, 25, and 9; predicted/output
azure counts 18/18, 24/24, and 16/16.

**Implementation.** `solution.py` performs the two BFS traversals, copies the
input, and changes only zero-valued cells satisfying the distance equality. It
returns the input unchanged if either endpoint is absent or disconnected.

**Alternatives rejected.** “Fill the whole connected corridor” fails on the
third example because it would color the two-cell dead-end spur. “Color one
shortest path” fails on the first and third examples because both tied routes are
shown. The remaining uncertainty is whether a hidden case uses a non-`5` wall
color, but every visible barrier is `5` and all other visible values are path
background, endpoints, or output color.
