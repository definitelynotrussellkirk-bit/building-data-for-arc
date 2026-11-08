# Solve notes — 0162460030af

This is a human work log based only on the visible examples emitted by `solve_episode.py prepare`. I had earlier rule exposure during the generator review, so this is not a blind solve; I did not consult generator code, Racket source, reference solutions, private labels, or prior solve explanations during this episode.

## Hypothesis

Treat every nonzero 4-connected region as one object, regardless of its original color or shape. Sort objects by their leftmost occupied column. Preserve the background and recolor whole objects in an alternating `2, 8, 2, 8, ...` pattern whose rightmost object is always `8`.

Visible checks:

- Example 0 has six objects, so left-to-right colors are `2,8,2,8,2,8`.
- Example 1 has five objects, so left-to-right colors are `8,2,8,2,8`; this rules out always anchoring `2` on the left.
- Example 2 uses six differently colored L-shaped objects and still follows `2,8,2,8,2,8`, showing that source color and exact shape are irrelevant.

## Implementation

Flood-fill nonzero cells with 4-neighbor connectivity, sort components by minimum column, deep-copy the grid, and assign object index `i` color `8` exactly when `(number_of_objects - i)` is odd; otherwise assign `2`.
