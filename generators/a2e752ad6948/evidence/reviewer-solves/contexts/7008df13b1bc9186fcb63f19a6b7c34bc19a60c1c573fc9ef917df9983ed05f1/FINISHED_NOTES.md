# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Observed two or more hollow monochrome rectangular frames in every visible input.
Each frame contains one differently colored interior marker.  Comparing all three
training outputs showed a common invariant: the full interior becomes a
checkerboard of frame color and marker color, and the *top-left interior cell is
always the marker color*.  The marker's original location does not determine
phase and need not be preserved.

Implemented a generic solver that finds 4-connected monochrome components whose
cells equal an exact rectangle perimeter, reads the unique different nonzero
interior color, and fills the interior checkerboard from top-left.  This avoids
assuming a fixed object count, frame size, placement, or palette.
