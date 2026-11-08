# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — enclosed-background fill

Earlier exposure: none. I had not opened this task's generator, rule, notes,
solutions, labels, or audit evidence.

Visible pattern: every changed cell is a zero in a 4-connected background region
that cannot reach the grid border. The output fills such a hole with the color of
its surrounding boundary. Train 0 is a hollow rectangle; train 2 has two hollow
rectangles. Train 1 is decisive against a bounding-box rule: row 3, column 1 lies
inside the object's bounding box but remains zero because it is outside the
closed boundary, while the three genuinely enclosed cells are filled.

Probe before implementation: importing the untouched solution and checking all
visible training pairs failed with `NotImplementedError`, confirming the harness
would detect the missing behavior.

Implementation: flood-fill all zero cells reachable from the border using
4-neighbor connectivity. Each remaining zero component is a hole. Fill it with
the most frequent nonzero color on its 4-neighbor boundary. The visible tasks use
one boundary color, while this tie-safe choice also handles separate differently
colored closed objects.

Predictions: in query 0, fill the two-by-two interior of the left rectangle and
leave the open right-hand C-shape unchanged. In query 1, fill the 4-by-3 interior
of the rectangle. Remaining uncertainty: diagonal leakage conventions are not
explicitly contrasted; 4-connectivity is consistent with all visible examples
and standard cell-edge enclosure.
