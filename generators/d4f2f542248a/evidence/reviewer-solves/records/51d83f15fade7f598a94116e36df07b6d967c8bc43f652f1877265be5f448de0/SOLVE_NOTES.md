# Blind solve notes

I used only the visible examples in `solve-blind/challenge.json` and small Python experiments over those grids.

## Observations

- Color 5 forms impassable maze walls; colors 2 and 3 are endpoints.
- Changed cells are zeros recolored to 8.
- A single arbitrary shortest path does not match: some zero cells on one shortest route remain 0.
- For each training example, the 8-cells are exactly the interior cells shared by **every** shortest 4-neighbor route between 3 and 2.
  - Example 0 has four shortest routes; six interior cells are common to all four.
  - Example 1 has three shortest routes; twelve interior cells are common to all three.
  - Example 2 has two shortest routes; fourteen interior cells are common to both.

## Algorithm

1. Breadth-first search from each endpoint through every non-5 cell.
2. Keep cells whose two distances sum to the endpoint-to-endpoint shortest distance; these form the shortest-path DAG.
3. Count shortest prefixes from color 3 and shortest suffixes from color 2.
4. A shortest-path cell is mandatory exactly when `prefix_count * suffix_count == total_shortest_paths`.
5. Recolor mandatory zero cells to 8, preserving the endpoints and walls.

This hypothesis reproduces all three visible training outputs exactly. No reference rule, private label, generator source, earlier solution explanation, or audit record was consulted.
