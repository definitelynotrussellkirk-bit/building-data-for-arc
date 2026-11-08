# Solve work log

## Exposure record

Before the assignment draw I opened only packet-level documentation (`WELCOME.md`,
`RETURN-GUIDE.md`, `ARC-DESIGN.md`, and repository overview files). I did **not**
open task `671a9af906aa`'s generator, canonical rule, notes, solutions, labels, or
any task-specific prior record. I also had not opened the repair target. The
hypothesis below comes only from the five visible demonstrations.

## Revision 1 — pairwise maze paths

**Observation.** Color 8 forms maze walls. The remaining cells form corridors
containing exactly one marker of each color 2, 3, 4, and 5. Output color 7 always
replaces corridor zeros while the four colored markers are preserved.

**Hypothesis.** Treat non-8 cells as an orthogonal graph. Connect marker 2 to 3
and marker 4 to 5. Recolor zero cells on each connected pair's path with 7; if a
pair is disconnected, do nothing for that pair.

**Probes from the visible examples.**

- Example 1 has adjacent 4 and 5, so that pair contributes no 7s; the displayed
  7s are exactly the corridor from 2 to 3.
- Example 2 forces the 2-to-3 route through the cell occupied by 5. This explains
  why the output preserves 5 but colors the surrounding route, and shows that
  other endpoint colors remain traversable.
- Example 4 leaves the grid unchanged because both designated pairs are in
  disconnected corridor components.
- Example 0 rules out simply filling a connected component: two zero cells on a
  dead branch remain 0. It is the union of the designated pair paths instead.

**Implementation choice.** Use breadth-first search through every non-8 cell for
pairs `(2, 3)` and `(4, 5)`, then recolor only path cells whose original value is
0. The demonstrations appear to use unique maze paths; BFS also gives a stable
shortest path if a future visible instance contains a cycle.

**Remaining uncertainty.** If a hidden instance deliberately contains multiple
equal shortest routes, the examples do not establish whether one route or all
shortest-route cells should be colored. The maze-like demonstrations strongly
suggest unique paths.
