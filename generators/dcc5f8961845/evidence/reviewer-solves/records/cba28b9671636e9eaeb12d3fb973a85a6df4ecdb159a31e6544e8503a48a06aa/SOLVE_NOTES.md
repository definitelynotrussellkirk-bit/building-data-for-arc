# Solve work log

I had not seen task `dcc5f8961845`, its generator, its Racket rule, private labels,
or any earlier solution explanation before this blind episode. I used only the
visible examples printed by `python3 review.py blind prepare` and local scratch
calculations on those grids.

## Revision 1 — color-sum operation code

The lower, compact nonzero pattern is cropped from the otherwise empty canvas.
The detached nonzero cells in row 0 form a key. Their color values sum to a code:

- train 0: `2 + 4 = 6`; the output is an up/down flip of the crop;
- train 1: `3 + 4 = 7`; the output is a 90-degree clockwise rotation;
- train 2: `3`; the output is a main-diagonal transpose.

Those three observations fit a systematic eight-way dihedral lookup:

`0 identity, 1 anti-transpose, 2 rotate 180, 3 transpose, 4 left/right flip,
5 rotate 90 counterclockwise, 6 up/down flip, 7 rotate 90 clockwise`.

This predicts query 0's single gray key (`5`) means rotate the 2x3 payload 90
degrees counterclockwise, and query 1's two blue cells (`1+1=2`) mean rotate its
4x4 payload 180 degrees. I considered rules based on marker position, payload
location, canonical lexicographic orientation, and selecting a matching payload
color, but they did not explain all three visible transforms. The exact sums and
the coherent dihedral table were the strongest common rule.

The implementation reads the key from row 0, crops all nonzero cells below it,
and applies that lookup. Remaining uncertainty: only three of the eight codes
are demonstrated, so the unobserved table entries are an inferred systematic
completion rather than directly visible facts.
