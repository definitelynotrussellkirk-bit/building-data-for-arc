# Solve work log

## Exposure declaration before solving

I had already inspected and repaired this task's generator and had seen the selected rule during the required review work. This is therefore an exposed post-repair solve, not a blind solve. During this solve episode I did not reopen the generator, Racket source, reference solutions, or private labels; I used only the visible examples printed by `solve prepare`.

## Revision 1 — opposite-corner bounding box

Every visible input has exactly two blue cells. Their inclusive row separation is 3 in all three demonstrations, while their inclusive column separations are 6, 3, and 4. The outputs are solid color-8 rectangles with exactly those dimensions. The diagonal direction changes in the third example, so orientation does not alter the rule.

Implemented: locate the two color-1 cells; return an all-8 grid whose height is `abs(r1-r0)+1` and width is `abs(c1-c0)+1`.

Remaining uncertainty before checking: none within the visible grammar beyond malformed inputs, which the solver rejects explicitly.
