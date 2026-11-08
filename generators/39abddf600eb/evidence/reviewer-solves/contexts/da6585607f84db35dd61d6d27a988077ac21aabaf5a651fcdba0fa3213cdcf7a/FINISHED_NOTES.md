# Solve notes

This is a human work log based only on `solve/challenge.json`. I had earlier rule exposure from the generator review, so this is an exposed visible-only solve rather than a blind solve; I did not reopen the generator, Racket source, canonical answers, or private labels during this episode.

## Revision 1

Hypothesis from the three visible training pairs: the repeated nonzero color forms an inset rectangular frame, and the other two nonzero interior cells are seeds. The output preserves the input and colors every strict-interior cell `9` exactly when its Manhattan distance to the two seeds is equal.

Checks against the visible examples:

- Vertically aligned seeds produce a horizontal bisector across the frame interior.
- Horizontally aligned seeds produce a vertical bisector.
- A diagonal pair produces two axis-aligned rays, matching the equality locus of the two Manhattan-distance functions.

Implementation plan: identify the high-frequency frame color, recover its bounds, find the two non-frame interior seeds, and test the distance equality for every strict-interior cell. Preserve all other pixels.
