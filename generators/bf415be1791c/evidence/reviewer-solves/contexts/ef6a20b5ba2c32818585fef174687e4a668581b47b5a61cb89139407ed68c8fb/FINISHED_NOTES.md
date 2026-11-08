# Solve work log

## Exposure declaration

I had earlier exposure to this task family through the prior v2.0.0 review and
solve, so this is **not blind**. During this fresh episode I used only the
visible examples in `solve/challenge.json`; I did not consult the Racket rule,
generator source, reference solutions, private labels, or the prior solution.

## Revision 1 — reflect every magenta cell across the gray divider

All three examples contain exactly one full-height gray (`5`) column. Every
magenta (`6`) input cell lies to its left. The output keeps the complete input
and adds one cyan (`8`) cell at the horizontal reflection of each magenta cell:
for divider column `d`, source column `c` maps to `2*d-c` on the same row.
The number of added cyan cells equals the magenta count in all three examples
(10, 5, and 10).

The examples also distinguish nearby rules. Example 0 has disconnected magenta
components of different sizes and all of them are reflected, so this is not
"largest component only" or a small-component filter. Colored distractors such
as `1`, `3`, `7`, and `9` are preserved without general reflection, so color `6`
is the source role. Source magenta remains in place, ruling out a move. I wrote
a direct per-cell transform that finds the unique full-height gray column,
copies the grid, and paints cyan only into in-bounds blank mirror cells.

Remaining uncertainty: masked query labels are unavailable. The implementation
assumes the visible invariant of one full-height gray divider and preserves an
occupied mirror target rather than overwriting it.
