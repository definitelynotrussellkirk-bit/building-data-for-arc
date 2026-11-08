# Solve work log

## Exposure declaration before solving

I had already inspected the assigned generator and canonical rule while performing the required repair, so this is an exposed post-repair solve, not a blind solve. During this solve I used only the visible examples in `solve/README.md` / `challenge.json` and my own Python. I did not reopen the generator, Racket rule, reference solution, private query labels, or prior solution explanations.

## Revision 1 — four-quadrant positional overlay

The output height and width are each half the input dimensions. I split each input into equal TL, TR, BL, and BR quadrants and compared values at the same local coordinate.

The visible examples give direct precedence witnesses:

- Train 0 local `(0,1)`: TR=4 and BL=1, output 4, so TR beats BL.
- Train 0 local `(1,1)`: TL=3, BL=1, BR=6, output 1, so BL beats BR and TL.
- Train 0 local `(2,1)`: TL=3 and BR=6, output 6, so BR beats TL.
- Cells with only one nonzero quadrant preserve that color; all-zero coordinates remain 0.

These comparisons determine the high-to-low order `TR > BL > BR > TL`. The implementation therefore chooses the first nonzero value in that order at every local coordinate. I considered simple union, color-frequency selection, and fixed quadrant selection, but the conflicting cells above reject them. Remaining uncertainty is limited to masked-query scoring; the rule is fully specified by the visible conflicts.
