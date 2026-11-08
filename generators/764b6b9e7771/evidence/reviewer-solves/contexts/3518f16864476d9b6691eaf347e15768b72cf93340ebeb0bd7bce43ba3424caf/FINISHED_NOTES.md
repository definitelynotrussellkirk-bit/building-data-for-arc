# Blind solve: 764b6b9e7771

Earlier rule exposure: no. Reference consulted during solve: no.
Only `solve-blind/challenge.json` was inspected; no generator, task notes,
canonical records, reference solutions, or private labels were read.

## Revision 1 — directed orthogonal waypoint path

The visible examples preserve every nonzero input cell and insert color 8
between a directed start and a gray wall. The adjacent 2 then 1 cells define
the initial travel direction. The path reaches a 4 or 6 point, turns by 90
degrees toward the next unvisited aligned point, and ends at color 5.
The turning direction is not a fixed handedness: both left and right turns
occur at the same color in visible example 3. Geometry and excluding already
visited points give a unique continuation in the supplied examples.

The implementation traces the initial ray from 1, paints only zero cells 8,
and at each waypoint requires exactly one perpendicular ray to an unvisited
4, 6, or 5. It preserves the original points and stops at the wall. This is
the first genuine solution attempt; no deliberate failing revision was made.

Uncertainty: the examples do not establish how to resolve a future input
with two unvisited perpendicular targets. The solver raises an explicit
error for that case instead of inventing an unsupported tie rule. Masked
query correctness will remain unknown until independent maintainer scoring.
