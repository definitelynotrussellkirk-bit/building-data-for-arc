# Solve work log

## Exposure record

I had seen the intended rule earlier while reviewing the assigned generator, so this is an `earlier-exposure=yes` solve. After `prepare`, I consulted only `solve/challenge.json`, this solve workspace's instructions, and my own calculations. I did not reopen the generator, Racket rule, private labels, reference solutions, blind-solve notes, or earlier solution code.

## Revision 1

Hypothesis from the four visible training pairs:

1. The blue `1` in a canvas corner selects how many clockwise quarter-turns to apply to the cropped green (`3`) shape: top-left = 0, top-right = 1, bottom-right = 2, bottom-left = 3.
2. Crop the red (`2`) and transformed green shapes to their bounding boxes and align their upper-left corners on the smallest canvas containing both.
3. Output cyan (`8`) exactly where one, but not both, masks is occupied (XOR); output `0` elsewhere.

Visible checks performed before coding:

- Pair 1 (top-left) needs no rotation. XOR of the 3x3 green mask with the top-left-padded 3x2 red mask exactly yields the shown output.
- Pair 2 (top-right) becomes exact only after rotating green 90 degrees clockwise.
- Pair 3 (bottom-right) uses 180 degrees; its horizontal green bar XOR vertical red bar matches the shown L-like output.
- Pair 4 (bottom-left) uses 270 degrees clockwise; the resulting 3x3 XOR matches all visible cyan cells.

Rejected alternatives: rotating the red shape instead, using overlap/intersection, and selecting rotation from object placement rather than the blue corner all contradict at least one visible pair.

Implementation: crop binary masks, rotate green, top-left-pad implicitly while computing the maximum bounding canvas, and emit XOR in color 8.

Remaining uncertainty before the check: none about the visible examples; private tests could still include malformed inputs outside the demonstrated grammar, which the solver deliberately rejects rather than guessing.
