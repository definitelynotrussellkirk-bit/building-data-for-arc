# Solve notes

This is a human work log. I had already inspected the assigned generator and canonical rule during the required generator-review phase, so this is **not a blind solve**. During this solve phase I consulted only `solve/challenge.json`; I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Visible-example observations

- Every input is a square, solid-color field with one differently colored interior dot.
- The output preserves the dot and paints color 1 in the dot's column above and below it.
- The top and bottom endpoints extend horizontally to opposite sides.
- In visible examples where `dot_row == dot_col`, the top arm goes right and the bottom arm goes left.
- In visible examples where `dot_row != dot_col`, the top arm goes left and the bottom arm goes right.
- The two visible queries instantiate those two branches directly: `(1,1)` on a 7x7 grid and `(1,7)` on a 9x9 grid.

## Implementation decision

Find the background from the top-left cell, locate the unique non-background dot, copy the grid, paint the dot column with 1 while preserving the dot, then route the top and bottom horizontal arms according to the equality test above. The implementation supports any rectangular dimensions even though all visible examples are square.
