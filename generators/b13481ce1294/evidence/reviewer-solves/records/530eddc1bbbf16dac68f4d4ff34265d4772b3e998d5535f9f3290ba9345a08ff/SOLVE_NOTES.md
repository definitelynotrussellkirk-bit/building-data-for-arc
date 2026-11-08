# Solve work log

I had not opened this task's generator, canonical rule, private labels, prior
solutions, or audit records. I only used the visible grids produced by blind
preparation. I had no earlier exposure to this task's rule.

## Revision 1 — symmetric-difference overlay

All inputs are two equal-width panels separated by a solid vertical column of
color 8. The output has the panel dimensions. I compared corresponding cells:

- when exactly one side is nonzero, the output copies that nonzero color;
- when both sides are zero, the output is zero;
- when both sides are nonzero, even with different colors, the output is zero.

This is the cellwise symmetric difference (exclusive-or) of the two panels.
For example, train 0 row 0 has left `[0,2,2,0]` and right `[0,6,0,2]`,
which yields `[0,0,2,2]`; the overlapping nonzero pair `(2,6)` is erased.
Train 1 row 2 has disjoint colored cells and therefore becomes `[4,0,4,9]`.

I considered ordinary overlay, color matching, and subtraction of one side from
the other. Ordinary overlay fails at every occupied overlap; matching-only fails
because lone cells are retained; directional subtraction fails because lone
cells from either side survive. The symmetric rule fits every visible cell and
is invariant to which panel supplies the surviving color.

The implementation splits at the middle separator and applies this rule to each
paired cell. Remaining uncertainty is limited to unseen malformed layouts; every
visible instance uses one separator and equal panels.
