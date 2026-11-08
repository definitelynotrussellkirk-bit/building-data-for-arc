# Solve work log

## Exposure declaration before solving

I had already inspected this task's selected rule and generator while repairing it, so this is **not blind**. During this solve episode I did not reopen the generator, Racket rule, reference solutions, private labels, or earlier solution explanations. I used only the visible examples printed by `solve_episode.py prepare` and the local solution/check interface.

## Revision 1 — local orthogonal degree

Across the four demonstrations, output cells are a subset of the gray input cells and the grid shape is unchanged. A gray cell survives precisely when it has exactly one orthogonal gray neighbor:

- the two-cell component in example 0 remains entirely because both cells have degree 1;
- interiors of longer paths disappear while their two endpoints remain;
- the isolated gray cell in example 1 disappears because it has degree 0;
- the T-junction in example 2 keeps its three leaves and removes the degree-3 center;
- example 3 separately confirms straight-path endpoints and removal of an isolated cell.

This rules out the weaker component-level hypothesis “keep two extreme cells per object”: a T has three valid leaves. It also rules out “keep degree at most one,” because isolated cells are removed.

I implemented a direct scan that counts same-color north/south/east/west neighbors and copies a nonzero cell only when that count equals one. The visible inputs only use gray 5, but comparing to the same cell color makes the implementation color-generic without changing the observed behavior.

Expected visible-query behavior before checking:

- query 0: keep the two endpoints of the five-cell L-shaped path and both cells of the separate pair;
- query 1: drop the singleton, keep the two endpoints of the upper zig-zag path, and keep all three leaves of the lower T.

No alternate revision was needed after this hypothesis fit every visible demonstration.
