# Solve work log

## Exposure disclosure

Before this solve episode I had already inspected the generator and canonical
rule while performing the assigned repair, so this is **not** an independent
blind solve.  After `solve prepare`, I did not reopen the generator, Racket
rule, reference solutions, private labels, or earlier solution notes.  The
implementation below was checked only against the visible examples.

## Revision 1

Hypothesis from the four visible demonstrations:

- Colors 2, 3, and 4 define an ordered source coordinate frame: 2 is the
  origin, 2→3 is local axis `u`, and 2→4 is local axis `v`.
- Colors 5, 6, and 7 define the corresponding target frame: 5 is the origin,
  5→6 is `u`, and 5→7 is `v`.
- The color-8 cells within three local steps of color 2 are a motif.  More
  distant color-8 cells are distractors (train example 2 visibly contains one
  at local Chebyshev distance 4).
- Project the motif into source-local coordinates, take its axis-aligned
  bounding box, and draw that box's perimeter in color 8 in target-local
  coordinates.  Painting is allowed to replace a target marker when that
  marker lies on the perimeter, as train examples 0 and 3 show for color 7.

I implemented this directly with cardinal-vector dot products, preserving all
input cells except the painted target perimeter.  The main alternatives I
considered were copying the motif itself, drawing only the corners, or filling
the full rectangle; each conflicts with visible output cells.  Remaining
uncertainty before checking: whether the source neighborhood cutoff is exactly
three local steps or merely separates the one visible distant distractor.  All
visible motifs fit the radius-three interpretation, including the larger box in
train example 2.
