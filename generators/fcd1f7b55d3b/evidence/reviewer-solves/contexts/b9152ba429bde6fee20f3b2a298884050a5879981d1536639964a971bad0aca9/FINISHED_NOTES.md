# Solve work log

## Exposure statement before solving

I had not opened this task's generator, Racket rule, notes, reference solutions,
private labels, audit evidence, or earlier solution explanations. I used only the
visible examples produced by `python3 review.py blind prepare` and the public
files in this solve directory.

## Revision 1 — paired points define solid rectangles

**Observation.** In every training example, each output-colored object starts as
exactly two input cells of the same color. The output fills the inclusive
axis-aligned bounding rectangle whose opposite corners are those two cells. For
example, training example 0 has color 3 at `(0,1)` and `(2,3)`, producing the
3-by-3 rectangle spanning rows 0–2 and columns 1–3. Training example 3 has color
6 at `(4,8)` and `(7,6)`, producing a 4-by-3 rectangle spanning rows 4–7 and
columns 6–8.

**Distractor evidence.** A nonzero color that does not occur exactly twice is
removed rather than copied. Color 4 occurs once in training example 1 and is
absent from the output; color 1 occurs three times in training example 2 and is
also absent. This distinguishes the rule from “fill a bounding box for every
nonzero color” and from “copy all original marks, then expand pairs.”

**Program.** Start with an all-zero grid of the same shape. Collect positions for
each nonzero color. For every color with exactly two positions, fill its inclusive
row/column bounding box with that color. Ignore all other colors.

**Alternatives considered.** The points could have represented only diagonal
corners of fixed 3-by-3 squares, but examples include 4-by-4, 4-by-3, 3-by-5,
and other rectangle sizes. They could have selected the two most frequent
nonzero colors, but examples retain three separate two-cell colors. Thus count
exactly two plus an arbitrary-size bounding rectangle is the simplest rule that
fits all visible examples.

**Remaining uncertainty.** No visible example contains overlapping rectangles,
so overwrite priority is unspecified. The generated examples appear designed to
avoid overlap; the implementation uses normal color encounter order if it occurs.
