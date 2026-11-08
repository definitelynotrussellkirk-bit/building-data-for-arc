# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — rank rectangular objects by size

Earlier exposure before this solve: none to the task's generator, rule, notes,
reference solutions, or private labels. I only read the visible examples emitted
by `python3 review.py blind prepare` and the public solve files.

Hypothesis: every gray 4-connected object is a rectangular frame or solid
rectangle. Recolor the objects in descending bounding-box area using the fixed
rank palette 2, 4, 6, 7. This explains the nested examples and, importantly,
the examples where several objects have the same gray-cell count but different
bounding boxes: the largest bounding rectangle is red (2), followed by yellow
(4), magenta (6), and orange (7).

Probe: I wrote a visible-example regression script in `/tmp/test_blind_visible.py`.
Before implementation it failed at the untouched `NotImplementedError`, proving
that the check exercised the solution. The implementation finds 4-connected
nonzero components, ranks them by bounding-box area, and recolors their cells.

Alternatives considered: rank by raw pixel count (rejected because train examples
1 and 3 contain equal-perimeter objects with different output colors); rank by
position (rejected because positions vary); infer nesting depth only (rejected
because separate objects receive the same size ranking).

Remaining uncertainty: the visible palette defines four ranks only. Both query
inputs contain at most four components, so no extrapolation beyond rank four is
needed.
