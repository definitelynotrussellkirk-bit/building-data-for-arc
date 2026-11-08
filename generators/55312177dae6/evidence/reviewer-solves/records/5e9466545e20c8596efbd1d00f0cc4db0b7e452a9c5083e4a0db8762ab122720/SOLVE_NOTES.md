# Solve notes — 55312177dae6

This is a human work log based on the visible challenge examples. I had earlier
rule exposure while repairing this same generator, so this is an exposed
post-repair solve, not a blind solve; I did not consult the generator, Racket
source, reference solution, or private labels during this solve episode.

## Revision 1

Hypothesis from the four visible pairs: split the blue cells into 4-connected
objects, normalize each object by translation, compare all four rotations, and
find the single rotation-equivalence class represented twice. Render the
lexicographically smallest normalized rotation of that class in cyan (8),
cropped to its bounding box.

Implementation details:

- foreground connectivity is cardinal (4-neighbor), matching the visibly
  separated objects;
- each shape is translation-normalized before and after rotation;
- canonical orientation is the lexicographically least of four rotations;
- the first class with frequency at least two is rendered, because every
  visible lesson has one unique repeated class.

No revision was needed after visible-example checking.
