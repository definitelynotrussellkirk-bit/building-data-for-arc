# Post-repair visible solve notes

## Revision 1

Observed that exactly one corner contains a value in 1–4 and that this cell is preserved rather than extended. Across examples the corner value determines a shared direction for every other colored non-5 cell:

- 1 = upward
- 2 = rightward
- 3 = downward
- 4 = leftward

Each nonzero non-5 non-marker cell emits its own color repeatedly in that direction. A color-5 cell stops the ray before the 5 and remains unchanged; other colored cells do not stop a ray. The output keeps all original cells and overlays the rays in row-major emitter order. I implemented that rule directly.

I had earlier rule exposure during generator review, so this is not a blind inference claim. During this solve phase I used only the prepared visible examples and did not reopen the generator, canonical data, or Racket source.
