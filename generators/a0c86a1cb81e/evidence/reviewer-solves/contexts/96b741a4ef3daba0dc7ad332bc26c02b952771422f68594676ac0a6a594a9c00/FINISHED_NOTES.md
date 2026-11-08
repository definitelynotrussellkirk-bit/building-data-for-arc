# Solve work log

I had not opened task `a0c86a1cb81e`'s generator, Racket rule, reference
solutions, private labels, notes, or prior solution explanations before this
blind episode. I had only read the packet-level instructions and the visible
`challenge.json` produced by `solve_episode.py blind prepare`.

## Revision 1 — orthogonal turns in green paths

Each nonzero connected component is a one-cell-wide 4-connected path colored
3. Comparing all three visible pairs, the cells changed from 3 to 6 are exactly
the path's 90-degree turn cells: each has at least one vertical green neighbor
and at least one horizontal green neighbor. Straight interior cells and endpoints
stay 3.

Checks against the visible examples:

- Training 1: the five-cell zigzag has two turns and the four-cell L has one.
- Training 2: the top L has one turn and the lower bent path has two.
- Training 3: each highlighted cell is the unique corner of an L, or one of the
  two corners in the five-cell zigzag.

I implemented the local predicate against the original grid and copy the grid
before recoloring. This avoids recolored 6 cells influencing later neighbor
checks. Remaining uncertainty: the examples contain no branches or thick
objects, so the most literal learned rule is the local turn predicate rather
than a more restrictive component-level path validator.
