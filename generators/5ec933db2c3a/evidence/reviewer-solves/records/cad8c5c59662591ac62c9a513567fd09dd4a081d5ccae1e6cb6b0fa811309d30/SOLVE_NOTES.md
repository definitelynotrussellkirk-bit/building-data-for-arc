# Solve work log

## Prior exposure

I had already inspected and repaired this task's generator and selected authority before this required post-repair solve. Therefore this is explicitly **not blind**. During this solve I used only `solve/challenge.json`, my own implementation, and visible-example feedback; I did not reopen the generator, Racket source, reference solutions, private labels, or prior solution notes.

## Visible-example hypothesis

Every input has a full-height color-9 divider. The left side contains a small multicolor template; the right side is the board and is also the output shape.

Comparing the three visible input/output pairs shows that the output keeps the board unchanged except where a 90-degree rotation of the cropped template is present with exactly two occupied template cells missing. Those two zero cells are restored with the colors at the corresponding template positions. Important negative evidence in the visible examples:

- partial copies with one or three missing occupied cells stay unchanged;
- a nonzero board cell under a zero template position invalidates the window;
- all four rotations must be searched;
- a missing color-7 cell is restored as 7, not recolored to 2.

## Implementation

1. Find the sole full-height color-9 divider.
2. Crop the nonzero bounding box of the left panel to obtain the template.
3. Enumerate its four clockwise rotations.
4. Slide each rotated template over the board.
5. Accept a window only when every template-zero position overlays board zero, every occupied template position is either the same color or board zero, and exactly two occupied positions are zero.
6. Fill those two cells with their template colors, accumulating all valid matches, and return the board alone.

## Local visible check

The first implementation reproduced all three visible training outputs exactly. No revision was needed. The main remaining uncertainty before the official visible check was only whether overlapping valid windows should accumulate; the examples and natural rule both support idempotent accumulation, which the implementation uses.
