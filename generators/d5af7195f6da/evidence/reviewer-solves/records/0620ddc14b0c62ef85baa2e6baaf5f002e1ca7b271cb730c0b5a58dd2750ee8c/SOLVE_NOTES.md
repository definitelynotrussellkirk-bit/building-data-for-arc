# Solve notes

## Visible-example hypothesis

Color 5 is an impassable wall. Every nonzero, non-5 cell is a seed. For each
zero cell, compare four-neighbor shortest-path distances through non-5 cells to
all reachable seeds. Fill with the uniquely nearest **color**. Leave the cell 0
when no seed reaches it or when different colors tie.

The examples distinguish the key edge cases:

- examples 0 and 4 show a blank equal-distance frontier between distinct colors;
- examples 1 and 5 show that walls change shortest paths rather than merely
  partitioning Euclidean regions;
- examples 2 and 6 leave a seedless chamber unchanged;
- example 3 has two seeds of color 4, and cells tied between those two still
  become 4, so ties must be deduplicated by color rather than seed identity.

## Implementation

Run one BFS per seed through all cells except color 5. Preserve walls and seeds.
For each zero, take the minimum reachable distance and deduplicate the colors at
that minimum before deciding whether to paint it.

No reference source was consulted during this solve episode. I had already seen
the rule while reviewing the assigned generator, so this is intentionally not
claimed as blind.
