# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private query labels, audit records, or any earlier explanation. I used only the visible examples printed by `review.py blind prepare` and `challenge.json`.

## Revision 1 — directional rays around the divider

All examples contain one complete horizontal gray (`5`) divider. The non-gray markers are blue (`1`) and red (`2`). Comparing inputs and outputs showed a consistent directional rule:

- Above the divider, blue markers extend vertically upward to the outer edge, while red markers extend downward to the row immediately above the divider.
- Below the divider, blue markers extend vertically downward to the outer edge, while red markers extend upward to the row immediately below the divider.
- The divider and all original markers remain unchanged; only background cells on those vertical segments are colored.

I checked the hypothesis manually against every marker in all three visible examples, including markers already on an edge and markers immediately adjacent to a segment endpoint. An alternative "all colors extend toward/away from the nearest edge" was rejected because direction depends on color: blue always goes away from the divider and red always goes toward it.

Implementation locates the all-`5` row, copies the grid, collects the original markers, and fills the appropriate zero cells. Remaining uncertainty is limited to collisions between differently colored markers in the same column; none occur in the visible examples, so the implementation conservatively preserves any pre-existing nonzero cell.
