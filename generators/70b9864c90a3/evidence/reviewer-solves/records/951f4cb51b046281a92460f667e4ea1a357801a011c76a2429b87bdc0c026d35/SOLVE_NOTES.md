# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — equal-corner 3×3 completion

Earlier exposure: none. I had not opened this task's generator, canonical rule,
reference solution, labels, prior solve notes, or my assigned repair generator.

Observation: every changed cell is the center of a 3×3 window whose four corner
cells contain one equal nonzero color. The output copies that corner color into
an empty center. Other colors on the edge midpoints are irrelevant. Example 2
also shows that an already occupied center is preserved: the 4-corner box at
rows 0/2 and columns 0/2 has a 3 in its center and is unchanged.

Predicted additions:

- train 0: 4 at (1,2) and (4,5)
- train 1: 7 at (3,3), (4,6), and (6,1)
- train 2: 3 at (5,6) and 4 at (6,1)
- query 0: 2 at (1,3), (4,6), and (6,1)
- query 1: 3 at (2,1) and (3,5)

Implementation uses the original input for all corner tests and writes to a
copy, so additions do not cascade into new detections during the same pass.
Alternative hypotheses rejected by the visible pairs: completing arbitrary
rectangles (all demonstrated offsets are exactly two rows and columns), filling
mixed-color boxes, or overwriting a nonzero center.

TDD probe: `/tmp/test_blind_solution.py` loads all visible training pairs. It
first failed with the template's `NotImplementedError`; after implementing the
one-pass transform it should pass all three pairs.
