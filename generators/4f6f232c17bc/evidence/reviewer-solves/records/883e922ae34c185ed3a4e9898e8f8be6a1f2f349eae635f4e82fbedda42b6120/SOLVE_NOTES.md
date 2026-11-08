# Solve notes: 4f6f232c17bc

This is a human-authored visible-example work log. I had already inspected the
assigned task's generator and authority during the review, so this is an exposed
post-repair solve (`earlier-exposure=yes`), not a blind solve. During this solve I
used only the prepared visible examples and did not reopen the generator, Racket
rule, canonical source, private labels, or prior solution text.

## Hypothesis 1

Each input contains one full-height gray (`5`) column. Treat it as a vertical
reflection axis. For every blue (`1`) cell at `(row, col)`, put cyan (`8`) at
`(row, 2*axis-col)` in a fresh all-zero grid. Erase the divider, source object,
and other-color distractors. If a reflected cell would leave the grid, omit that
cell rather than rejecting the whole object.

Evidence from the visible demonstrations:

- Example 0 reflects a four-cell blue object from the left of column 5 to cyan
  on the right; the lone `4` disappears.
- Example 1 reflects from the right of column 4 to the left. Only three of six
  blue cells land in bounds, showing per-cell clipping; the `6` cells disappear.
- Example 2 reflects from the left of column 9 to the right. Two of five blue
  cells would land beyond column 13, so the remaining three appear at column 13;
  the `9` cells disappear.

The examples jointly rule out a fixed source side, a grid-center axis, copying
all nonzero colors, and all-or-nothing clipping. I implemented this hypothesis
as the first solution revision.
