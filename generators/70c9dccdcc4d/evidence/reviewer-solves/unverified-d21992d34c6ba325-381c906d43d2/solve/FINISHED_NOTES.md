# Solve notes

This is the exposed post-repair solve. I had already inspected the assigned rule
while repairing its generator, so prior rule exposure is **yes**; during this
solve I used only the prepared visible examples and did not reopen generator,
Racket, canonical, or private-label sources.

## Visible-example hypothesis

Each input contains two colored three-cell coordinate frames. Color 2 is the
source origin; its adjacent color-3 cell defines the local first axis and its
adjacent color-4 cell defines the second. Color 5 is the target origin, with
colors 6 and 7 defining the corresponding target axes.

The output preserves the input and copies only color-8 cells within local
Chebyshev distance three of the source origin. A source-local offset `(u, v)` is
placed in the target as `(v, u)`, so the motif is reflected across its local
diagonal. The visibly more distant 8-cells remain unchanged; they are negative
evidence against transforming every 8 in the grid.

## Implementation checks before submitting

- Frame discovery is orientation-independent and uses the colored axis roles.
- The input is deep-copied; source markers and distractors remain present.
- The radius test is local to the source frame, not raw grid distance.
- Only in-bounds transformed target cells are painted.
