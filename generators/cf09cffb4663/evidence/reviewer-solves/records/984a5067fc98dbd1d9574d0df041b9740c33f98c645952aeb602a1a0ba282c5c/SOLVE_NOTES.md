# Solve work log

Earlier exposure: none to this task's rule, generator, solutions, private labels, or prior notes. I inspected only `solve-blind/challenge.json`.

## Revision 1

Hypothesis: each input contains one or more thin color-1 line figures. Recolor a color-1 cell to 2 exactly when it is the center of a complete four-way orthogonal crossing: its immediate north, south, west, and east neighbors are all 1. Leave line endpoints, corners, T-junctions, disconnected strokes, and all other cells unchanged.

Evidence from the visible examples:
- Example 1 has one crossing of a vertical and horizontal stroke; only that shared cell becomes 2.
- Example 2 has two complete crossings; both centers become 2. The upper short horizontal figure lacks a complete vertical continuation and stays unchanged.
- Example 3 has one complete crossing and one separate horizontal stroke; only the crossing changes.

Probe: I wrote a small local test containing two plus-shaped crossings. The untouched template failed with `NotImplementedError`, then the implementation passed. Remaining uncertainty: the examples support the immediate-neighbor definition, but unseen data could conceivably intend intersections of longer inferred lines across gaps. I chose the direct local-crossing rule because every changed cell has all four adjacent arms and visible non-crossings do not.
