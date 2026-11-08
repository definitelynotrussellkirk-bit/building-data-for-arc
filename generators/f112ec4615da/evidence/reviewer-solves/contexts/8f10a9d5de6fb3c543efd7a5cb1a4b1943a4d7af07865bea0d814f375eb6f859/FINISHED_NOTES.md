# Post-repair solve notes

Human work log based only on the prepared visible examples. I had earlier rule
exposure from repairing this assigned generator, so this is intentionally not a
blind solve; I did not reopen the generator, Racket source, canonical ledger, or
private query labels during this solve.

## Revision 1

Each input has even dimensions and the output is exactly half as tall and half
as wide, suggesting four equal quadrants aligned by local coordinate. Every
quadrant uses zero plus one distinct foreground color. Comparing visible cells
with the labelled outputs gives a fixed nonzero overlay order:

1. top-right wins whenever occupied;
2. otherwise bottom-left wins;
3. otherwise bottom-right wins;
4. otherwise top-left wins;
5. all-zero positions stay zero.

For example, train 0 local coordinate `(0, 0)` contains TL=2, TR=6, BL=0,
BR=3 and outputs 6; `(0, 1)` contains TL=2, TR=0, BL=8, BR=3 and outputs 8.
The same role priority explains all output dimensions and colors without using
numeric color order. I implemented the direct coordinate-wise overlay and made
one ordinary solve attempt.
