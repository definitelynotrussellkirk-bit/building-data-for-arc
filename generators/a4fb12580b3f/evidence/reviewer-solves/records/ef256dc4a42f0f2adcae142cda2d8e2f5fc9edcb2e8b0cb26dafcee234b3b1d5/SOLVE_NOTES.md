# Solve work log

## Exposure declaration before solving

I had not opened task `a4fb12580b3f`'s generator, rule, notes, solutions, audit records, or private labels. I used only `solve-blind/challenge.json` and local Python reasoning. I had no earlier exposure to this task's rule.

## Revision 1 — 4-connected objects touching color 1

Hypothesis: color `1` is an anchor. For every monochromatic, nonzero, 4-connected component that shares an edge with any `1` cell, recolor the whole component to `4`; leave the anchor and all other components unchanged.

Evidence from the visible examples:

- Example 1 recolors exactly the nearby `3`, `7`, and `9` components, each edge-adjacent to the `1` object, while same-colored remote components remain unchanged.
- Example 2 recolors the `6` and `3` components on either side of the single `1`; the already-`4` component is unchanged, and remote components remain unchanged.
- Example 3 distinguishes 4-connectivity from diagonal connectivity: the upper `6` group is only diagonally related to the lower `6` group, and only the lower group touching `1` changes. The `5` above and `9` below the `1` also change.

Implementation: enumerate monochromatic 4-connected components, test whether any member is orthogonally adjacent to a `1`, and recolor qualifying cells to `4`. I intentionally do not merge diagonal cells or propagate through chains of different colors.

Remaining uncertainty before checking: a hidden case could define adjacency differently, but the split `6` groups in example 3 strongly support 4-connected components and edge contact.
