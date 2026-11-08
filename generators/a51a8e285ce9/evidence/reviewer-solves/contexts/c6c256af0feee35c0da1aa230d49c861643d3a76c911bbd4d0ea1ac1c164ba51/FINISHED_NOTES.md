# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — symmetry selector hypothesis

Earlier exposure: none. I used only the visible challenge prepared in this folder.

The grid has three equal-width panels separated at fixed positions by two full-height
color-8 columns. I did not infer separators by scanning every full-height 8 column,
because an object can itself be color 8 and touch a divider (visible in train 0).

Each panel contains an equal-area object. The third object is a rotated and/or
reflected copy of exactly one of the first two objects. The output is the matching
first/second object's cropped shape in its original orientation, recolored with the
third object's color. Evidence:

- train 0: first and third are identical;
- train 1: third is a horizontal reflection of the second;
- train 2: third is a reflected transpose of the first;
- train 3: third is a vertical reflection of the second.

The implementation crops binary masks, compares all eight dihedral symmetries, and
recolors the selected source. A local regression test covers all four visible pairs
plus the color-8 false-separator case. Remaining uncertainty: the visible data assumes
one non-background color per panel and exactly one symmetry match.
