# Solve notes

## Exposure declaration

I had already inspected and repaired this task's generator before this post-repair solve, so this is **not blind**. During the solve episode itself I did not reopen the generator, canonical ledger, Racket source, private labels, or prior solution explanations. I used only the visible examples printed by `solve_episode.py prepare`.

## Visible-example hypothesis

For each nonzero color independently:

1. Its three cells use exactly two row coordinates and two column coordinates.
2. Those coordinates define four corners of an axis-aligned rectangle.
3. The output adds the one absent row/column combination in the same color.
4. All other cells are unchanged.

The examples include adjacent coordinates as well as wider spans, so the rule depends only on the two-row/two-column corner relation, not a minimum rectangle size.

## Checks against the demonstrations

- Example 0: each of colors 4, 5, and 6 gains exactly its absent corner.
- Example 1: colors 7 and 9 gain one corner each; color 9 includes adjacent columns, confirming adjacency is allowed.
- Example 2: colors 1, 2, and 3 each complete a rectangle; several rectangles have a side span of one.

No competing operation is needed: there is no interior fill, fixed-corner convention, recoloring, movement, or deletion.

## Implementation

Group nonzero coordinates by color. For a color appearing three times, compute its two distinct rows and columns, enumerate the four Cartesian-product corners, and paint the unique missing one. Preserve the input otherwise.
