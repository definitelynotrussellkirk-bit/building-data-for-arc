# Solve work log

## Exposure and constraints

Before this solve I had not opened the task's generator, Racket rule, reference
solution, private labels, audit material, or earlier solution explanations.  I
used only the visible examples in `challenge.json` and local graph experiments.

## Revision 1 — mandatory shortest-path cells

**Observation.**  Color 5 behaves as a wall, while 0, 2, and 3 form a
4-neighbour passage graph.  Every output-only 8 lies on a shortest route between
the unique 2 and 3, but the output does not color all cells belonging to some
shortest route.

**Probe.**  For each training example I computed distances from both endpoints,
then counted all shortest paths and the number passing through each cell.  The
examples have 39, 20, and 4 shortest paths.  After excluding the endpoints, the
cells traversed by every shortest path match the shown 8 cells exactly in all
three examples.

**Implementation.**  `solution.py` uses two breadth-first searches, constructs
the shortest-path DAG, counts shortest prefixes and suffixes, and recolors a
zero cell iff `prefix_count * suffix_count == total_shortest_paths`.  Endpoints
and walls remain unchanged.  Unreachable or malformed endpoint cases return an
unchanged copy.

**Alternatives rejected.**  Coloring one arbitrary shortest route over-colors
examples 0–2.  Coloring only the initial corridor from either endpoint fails
because example 2's mandatory segment is internal to a branching route.

**Remaining uncertainty.**  The visible data establishes four-neighbour motion
and color 5 as the wall.  It does not demonstrate multiple endpoint pairs or an
unreachable pair; the implementation handles those conservatively without
altering the grid.
