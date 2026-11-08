# Solve work log

I used only the visible examples from `python3 review.py blind prepare`. I did
not open this task's generator, Racket rule, reference solution, private query
labels, audit evidence, or prior solution notes.

## Hypothesis

The isolated nonzero cell at input coordinate (0,0) is an instruction code. The
other nonzero cells form one object. Remove the instruction cell, crop the object
to its tight bounding box, then apply one of the eight square-grid symmetries:

1. identity;
2. rotate 90° clockwise;
3. rotate 180°;
4. rotate 90° counterclockwise;
5. reflect left/right;
6. reflect top/bottom;
7. transpose across the main diagonal;
8. reflect across the anti-diagonal (rotate 180°, then transpose).

Evidence by example:

- code 1 returns the 4×4 crop unchanged;
- code 2's 3×3 shape is consistent with a clockwise quarter-turn (it is also
  vertically symmetric enough that a top/bottom flip would fit that example
  alone, so the full eight-code pattern resolves the ambiguity);
- code 3 is a 180° turn;
- code 4 is a counterclockwise quarter-turn;
- code 5 mirrors a 4×2 crop left/right;
- code 6 flips a 2×5 crop top/bottom;
- code 7 transposes a 3×4 crop to 4×3;
- code 8 performs the anti-diagonal reflection on a 3×2 crop, yielding 2×3.

The implementation removes only (0,0), so an object may use the same color as the
instruction. It preserves all object colors and zeros inside the tight crop.

Predicted queries:

- query 0 (code 1): `[[1,1,1],[0,1,1],[0,1,1]]`;
- query 1 (code 2): `[[2,2,2],[2,2,0],[2,2,2]]`.

Remaining uncertainty is limited to malformed inputs (missing code or object),
which the visible task does not demonstrate.
