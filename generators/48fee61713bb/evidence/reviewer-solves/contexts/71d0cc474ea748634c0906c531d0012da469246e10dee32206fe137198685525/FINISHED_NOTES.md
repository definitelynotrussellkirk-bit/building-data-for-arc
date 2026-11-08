# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observations and hypothesis

Earlier exposure to this task's rule: none. I inspected only `challenge.json` and
files inside `solve-blind/`.

Each visible 30x30 input contains a 7x7 lattice of hollow 3x3 colored glyphs,
plus one solid border of color 1. Replacing each glyph by its color gives a
7x7 sparse grid. The output removes zero gaps while preserving the order of
colored cells. The packing direction is 90 degrees clockwise from the marked
border:

- bottom border -> pack each row left;
- top border -> pack each row right;
- left border -> pack each column up;
- right border -> pack each column down.

The output is cropped only along the packing axis to the longest packed line.
I checked this manually against all three training outputs: for example, in the
right-border example, each output column is exactly the corresponding decoded
input column with zeros removed and the remaining colors bottom-aligned.

## Revision 1

Implemented border detection, fixed-lattice glyph decoding, stable gap removal,
and alignment/cropping for all four possible border orientations. Remaining
uncertainty: the examples show the fixed 30x30 / 7x7 lattice, so the decoder is
intentionally specific to that visible format rather than guessing a broader
unseen layout.
