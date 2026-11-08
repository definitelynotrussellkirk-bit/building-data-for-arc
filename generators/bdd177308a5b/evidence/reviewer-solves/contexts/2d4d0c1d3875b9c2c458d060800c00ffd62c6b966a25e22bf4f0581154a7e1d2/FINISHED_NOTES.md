# Solve work log

## Exposure

Before this solve I read only the packet-level instructions and the visible challenge prepared by `review.py blind prepare`. I did not inspect the task's generator, canonical rule, reference solution, private query labels, or audit evidence.

## Revision 1 — framed exemplar and translated duplicate

Hypothesis: color 5 forms an L-shaped frame. The nonzero object in the open interior of that frame is an exemplar. Elsewhere in the grid there is one object with the same cell pattern under translation (same orientation); recolor that duplicate to 5 and leave everything else unchanged.

Evidence from the visible pairs:

- Example 0: the framed color-6 tetromino and the distant color-8 tetromino have identical normalized coordinates; only color 8 becomes 5.
- Example 1: the framed color-1 object matches the distant color-9 object.
- Example 2: the framed color-3 object matches the distant color-2 object.

The test queries preserve the same construction: query 0 frames color 7 and contains a translated color-8 copy; query 1 frames color 4 and contains a translated color-2 copy. Distractors can be rotationally congruent, so the program intentionally requires exact orientation rather than allowing rotations or reflections.

Probe: a local visible-example assertion harness initially failed on the `NotImplementedError`, as expected. I then implemented connected-component extraction, frame-interior detection, exact normalized-shape matching, and recoloring.

Remaining uncertainty: the visible examples show one 5-frame and one exact translated duplicate. The implementation raises a clear error if either is absent rather than guessing a rotation-based rule.
