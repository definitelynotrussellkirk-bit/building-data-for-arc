# Visible-only solve notes

Earlier exposure is **yes** because I repaired this task's generator before this required solve. During the solve episode I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, or private labels.

## Hypothesis 1

The outputs preserve every existing cell and fill certain zero cells. Every added cell is the center of a diagonal X: the four cells at offsets `(-1,-1), (-1,+1), (+1,-1), (+1,+1)` are all the same nonzero color, and the center receives that color. Partial Xs, unequal diagonal colors, and occupied centers stay unchanged. Orthogonal neighbors do not determine the fill.

I implemented a simultaneous scan over the original input so newly filled centers cannot trigger further changes during the same pass. This directly explains every visible change in all five demonstrations.
