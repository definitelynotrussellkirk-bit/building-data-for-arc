# Solve work log

I had not opened any generator, Racket rule, task notes, private labels, audit
records, or prior solution explanation before this solve. I used only the public
visible examples printed by `python3 review.py blind prepare` and my own small
array probes.

## Revision 1 — eight square symmetries

Hypothesis: the input is three 4×4 panels separated by color-8 columns. The
first two panels show the same foreground shape under one symmetry of the
square; the output is the third panel under that same symmetry, preserving its
foreground color.

Visible evidence:

- train 0: panel 2 is panel 1 rotated 180°, and the output is panel 3 rotated 180°;
- train 1: a 90° counter-clockwise rotation;
- train 2: a left-right reflection;
- train 3: a top-bottom reflection;
- train 4: reflection across the main diagonal (transpose).

I checked the candidate transformations with local Python arrays. The query-0
relation is the remaining diagonal reflection (equivalently left-right flip
followed by a 90° clockwise rotation). Query 1 is identity. Rather than encode
those two cases, `solution.py` enumerates all eight dihedral symmetries, matches
foreground masks from panels 1 and 2, and applies the matching indexed symmetry
to panel 3.

Alternatives considered: matching only bounding-box-normalized shapes would lose
the absolute placement information demonstrated by the examples; hard-coding
only rotations/reflections seen in training would omit the query-0 diagonal
reflection. Remaining uncertainty is only the usual ambiguity if the first
shape itself has multiple symmetries; the visible instances used here have a
matching transformation sufficient to reproduce all labelled examples.
