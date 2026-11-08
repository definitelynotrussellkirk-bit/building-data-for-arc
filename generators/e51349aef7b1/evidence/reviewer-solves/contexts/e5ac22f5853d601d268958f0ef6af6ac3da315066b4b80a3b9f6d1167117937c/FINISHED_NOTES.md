# Visible-only solve notes

I had already inspected this task's generator while repairing it, so this is an exposed solve, not a blind one. During this solve I used only the visible examples printed by `solve prepare`; I did not reopen the generator, Racket source, reference outputs, or private query labels.

The two full-height color-5 columns divide each input into three panels. Each panel contains one foreground object. Cropping removes placement offsets. The first panel is a transform legend: compare the cropped binary first and second objects to select a transform. Apply that transform to the cropped third object and recolor it with the second panel's foreground color.

The visible examples are consistent with the authority order identity, clockwise quarter-turn, half-turn, transpose, left-right reflection, then up-down reflection. The order matters for symmetric shapes. The implementation checks those transforms in that order and selects the first match.

Expected query reasoning:
- Query 0: cropped A maps to cropped B under a half-turn; half-turn the cropped six-cell C and recolor it 8.
- Query 1: cropped A maps to cropped B under a clockwise quarter-turn (also potentially a reflection for the L-shape, so first-match precedence matters); transform the cropped six-cell C and recolor it 2.
