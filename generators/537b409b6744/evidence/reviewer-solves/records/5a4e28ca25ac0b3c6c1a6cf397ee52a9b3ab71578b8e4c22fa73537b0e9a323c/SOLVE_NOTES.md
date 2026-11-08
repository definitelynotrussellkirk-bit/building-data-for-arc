# Solve work log

This is a human-authored work log. I had already inspected and repaired this task's generator and selected rule before this required post-repair solve, so **earlier rule exposure is yes**. During this solve episode I used only the freshly prepared visible examples and did not reopen the generator, Racket source, reference solutions, or private query labels.

## Revision 1 — nearest facing object passes through a larger wall

The modal color is background. The remaining same-color 4-connected components play three roles: a larger solid rectangular wall, the nearest smaller component that faces and overlaps it along one axis, and a farther distractor.

Visible evidence:

- Example 0 selects color 9 rather than the farther color 6 above a bottom wall. It erases color 9, cuts a same-width channel through the wall, grows the wall by one cell on both transverse sides, and places color 9 at the far edge.
- Example 1 is the vertical mirror: color 3 passes upward through the top wall while the farther L-shaped color 9 stays fixed.
- Example 2 is horizontal: color 4 is nearer than color 9 to the right wall, cuts a two-row channel, grows the wall one row above and below, and appears at the far edge.

Program plan: find modal background; extract same-color components; enumerate facing pairs whose blocker is solid and strictly larger in the transverse dimension; rank by smallest gap, then larger blocker; apply the channel/growth/move operation while preserving all nonselected objects. The boundary cases in all three examples place the mover inside the far edge of the carved wall channel; the program also handles an interior wall by placing it immediately beyond the wall.

Remaining uncertainty: the visible examples establish one-cell growth for mover transverse spans one and two. I use `max(1, span // 2)` as the natural generalization, although the prepared examples do not expose larger spans.
