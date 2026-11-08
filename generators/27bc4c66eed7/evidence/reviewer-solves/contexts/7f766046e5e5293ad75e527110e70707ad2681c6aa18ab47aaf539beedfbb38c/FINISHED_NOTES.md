# Solve work log

## Exposure

Before this solve I had not opened the task's generator, Racket rule, private
labels, prior solution explanations, or audit evidence. I used only the visible
examples printed by `python3 review.py blind prepare` and the generated README.

## Revision 1 — horizontal-run centers

Observation: every nonzero object is a horizontal run of a single color.  Runs
of length 3 or 5 are reduced to their unique center cell while preserving row,
color, and grid dimensions.  Train example 4 also contains two distinct color-6
runs on one row: a singleton at column 1 remains there, while the length-2 run
at columns 3–4 becomes column 4.  Train example 1 independently shows a
length-2 run at columns 0–1 becoming column 1.

Hypothesis: independently replace each maximal horizontal same-color run by one
cell at its center, resolving an even-length midpoint to the right.  Background
stays zero.  Runs are separated by background or a color change.

Implementation: scan each row left-to-right, identify maximal same-color
nonzero intervals `[start, end]`, and write the color at
`ceil((start + end) / 2)`, implemented as `(start + end + 1) // 2`.

Predicted queries:
- Query 0 keeps color 2 at `(2, 3)` and color 4 at `(4, 1)`.
- Query 1 keeps colors at `(1, 1)`, `(2, 6)`, `(3, 2)`, and `(3, 5)`.

Remaining uncertainty: the visible data only contains horizontal objects.  A
vertical/general connected-component interpretation is less parsimonious and
is not needed to fit any example.  Adjacent different nonzero colors do not
occur, but treating them as separate runs preserves the color-specific object
interpretation.
