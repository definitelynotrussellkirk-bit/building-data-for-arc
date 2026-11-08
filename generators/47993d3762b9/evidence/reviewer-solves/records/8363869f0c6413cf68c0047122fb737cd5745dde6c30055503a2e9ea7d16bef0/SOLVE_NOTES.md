# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial hypothesis

The nonzero cells separate naturally by color. For each color, the output clears
its original marks and places that color at the four corners of the smallest
axis-aligned rectangle containing all of its input cells. This explains both
sparse pairs (which become four corners) and larger diagonal/cross-like objects
(the interior or edge marks disappear). Degenerate boxes are handled by the set
of unique corners.

I checked this hypothesis manually against every visible training pair:
- color 9 in train 1 spans rows 0..2 and columns 3..5;
- color 7 in train 2 includes a redundant middle cell but becomes the corners of
  rows 6..8, columns 1..4;
- all three colors in train 3 and all three shapes in train 4 follow the same rule.

The implementation groups coordinates by color, computes row/column extrema,
and writes only the unique bounding-box corners into a fresh zero grid. Remaining
uncertainty is limited to unseen degenerate one-row or one-column cases; using a
set gives the natural two- or one-cell result.
