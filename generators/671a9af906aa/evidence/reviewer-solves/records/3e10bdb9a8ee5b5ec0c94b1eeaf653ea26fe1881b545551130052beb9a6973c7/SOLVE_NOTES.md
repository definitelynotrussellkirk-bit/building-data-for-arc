# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before `prepare`, I had inspected and repaired this task's generator and had seen the task's rule description. I therefore declare `earlier-exposure=yes`. During this solve episode I read only `solve/challenge.json`; I did not reopen the Racket rule, generator source, reference solutions, private query labels, or prior solution explanations.

## Revision 1 — stateful shortest path

The five visible examples suggest a maze transformation. Color 8 is a wall, 2 is the start, 3 is the goal, 4 is a key, 5 is a locked door, and route cells with value 0 are recolored 7. The fifth example is unchanged because its key is inaccessible behind the door, while examples 1 and 3 require collecting the key before crossing the door. Example 4 shows that the shortest path may bypass the key and door entirely.

Hypothesis: breadth-first search over `(row, column, has_key)` finds the shortest lawful orthogonal route. Entering color 4 sets `has_key`; entering color 5 is forbidden until then; color 8 is impassable. Reconstruct the first shortest route and paint only original zero cells 7, preserving all markers. If no goal state is reached, return an unchanged copy.

I used a fixed neighbor order `(down, up, right, left)` to make tied shortest paths deterministic. A local comparison against all five visible training outputs matched exactly, so I submitted this as the first genuine revision. Remaining uncertainty is only whether a hidden query contains equal-length alternatives whose intended tie-breaking differs; the displayed mazes appear tree-like, making shortest routes unique.
