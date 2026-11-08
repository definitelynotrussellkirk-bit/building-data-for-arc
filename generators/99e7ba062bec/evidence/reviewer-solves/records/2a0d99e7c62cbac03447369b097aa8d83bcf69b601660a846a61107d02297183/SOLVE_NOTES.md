# Solve work log

## Scope and exposure declaration

This is a human-authored work log. Before `solve_episode.py prepare`, I had already inspected the generator and authoritative rule as part of the required generator review, so earlier rule exposure is **yes**. During this solve phase I kept the generator source, Racket rule, canonical/reference solutions, private labels, and prior solution explanations closed. I used only `solve/challenge.json`, my own Python inspection, and visible-example feedback.

## Visible structure

Every input is a 5×17 grid containing three nonzero column bands separated by one or more entirely zero columns. Cropping each band gives panels A, B, and C. A and B use the same color; C uses another color. The output has C's color and cropped dimensions, suggesting that a geometric relation from A to B is transferred to C.

I printed only the visible challenge panels in compact row form. The five demonstrations gave these checks:

1. A `666/660` becomes B `60/66/66`; rotating A counterclockwise matches B, and rotating C counterclockwise gives the shown `9999/0090` output.
2. A `0005/0055/5550` becomes B `5000/5500/0555`; left-right reflection matches, and the same reflection matches the C output.
3. A `600/060/060/066` becomes B `066/060/060/600`; up-down reflection matches, and the same reflection matches the C output.
4. A `220/200/020/022` becomes B `2200/2022/0002`; transpose matches, and transposing C gives `5505/0055`.
5. A equals B and C equals the output, establishing the identity branch.

The two visible query relations are consistent with clockwise rotation and 180° rotation respectively, but the program should infer rather than hard-code those cases.

## Hypothesis

Split into three panels, crop them, enumerate the seven visible-example-compatible transforms in a stable order—identity, clockwise rotation, 180° rotation, counterclockwise rotation, left-right reflection, up-down reflection, transpose—and choose the first transform whose binary A mask equals B's mask. Apply that transform to the colored C panel and crop the result. Mask comparison avoids assigning meaning to the arbitrary A/B color, while applying the transform to C preserves C's color.

## Implementation choices

- Split only on columns that are zero in every row; this preserves internal zero cells inside a panel.
- Crop vertically and horizontally after splitting and after transformation.
- Compare nonzero masks rather than literal colors.
- Return fresh row lists and reject malformed inputs or unsupported relations explicitly.

## Remaining uncertainty before check

The visible generated examples appear transform-discriminative, so transform ordering should not affect them. If a symmetric A admitted multiple matches, visible examples alone would not fully identify a tie-breaking convention; the stable order above is the least arbitrary implementation and includes identity first.
