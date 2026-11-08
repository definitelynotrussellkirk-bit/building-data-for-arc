# Solve work log

## Prior exposure

Before this visible-only solve I had read only the packet-level instructions and the
public examples printed by `python3 review.py blind prepare`. I did not open this
task's generator, Racket rule, private labels, reference solutions, audit records,
or any earlier solution explanation.

## Hypotheses and probes

1. I first treated the two colored components as binary masks and tested simple
   top-left, corner-aligned Boolean combinations. The first example is exactly the
   cropped XOR of the color-2 and color-3 bounding-box masks, but an unrotated XOR
   does not explain the other examples.
2. I then compared the four blue-marker corners. They cover all four quarter-turns:
   top-left = 0 degrees, top-right = 90 degrees clockwise, bottom-right = 180
   degrees, and bottom-left = 90 degrees counterclockwise. Rotating only the
   color-3 mask by that code, top-left-aligning it with the unrotated color-2 mask,
   taking XOR, cropping all-zero outer rows/columns, and recoloring survivors 8
   reproduces every visible output exactly.
3. I implemented that rule without NumPy so the solution remains portable. A fully
   cancelled XOR is defensively represented as `[[0]]`; no visible example requires
   this fallback, and the task construction likely avoids it.

## Predicted queries

- Query 0: `[[8, 8, 0], [0, 0, 0], [0, 0, 8]]`.
- Query 1: `[[8, 8]]`.

The remaining uncertainty is only the all-cancelled edge case, which is not
identified by the visible examples.
