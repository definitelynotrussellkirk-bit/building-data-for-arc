# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — opposite corners define a rectangular frame

Earlier exposure: none. Before this solve I did not inspect this task's generator,
Racket rule, private labels, reference solution, or previous solution notes.

Observation: every nonzero color occurs exactly twice. In all three visible
training examples, those two cells are opposite corners of an axis-aligned
rectangle. The output leaves the grid size and background unchanged and colors
all cells on that rectangle's perimeter. A 2×2 rectangle therefore becomes a
solid 2×2 block; larger rectangles retain an empty interior.

Probe: I added a visible-example regression test that loads only `challenge.json`
and compares `solve` against all public training outputs. Before implementation it
failed with `NotImplementedError` for all three examples. I then implemented the
minimal rule: group nonzero cells by color, require exactly two cells, compute the
inclusive bounding box, and draw its top, bottom, left, and right edges into a copy
of the input.

Alternatives considered: drawing a filled rectangle is contradicted by the large
color-6 and color-8 examples; connecting the points by a path is contradicted by
all four sides appearing. Remaining uncertainty is limited to malformed inputs or
overlapping frames, neither of which occurs in the visible examples. The code
leaves colors with counts other than two unchanged and otherwise applies each
frame deterministically.
