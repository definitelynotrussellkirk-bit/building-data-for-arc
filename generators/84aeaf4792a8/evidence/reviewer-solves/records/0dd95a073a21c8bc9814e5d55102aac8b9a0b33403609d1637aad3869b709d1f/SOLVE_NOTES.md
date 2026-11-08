# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — component rotation-equivalence matrix

Prior exposure: I had not opened this task's generator, Racket rule, canonical row,
notes, reference solution, private labels, or audit evidence. I only read the packet
instructions and the visible examples emitted by `review.py blind prepare`.

Observation: every output is an `N × N` matrix where `N` is the number of
monochromatic 4-connected nonzero objects in input reading order. The diagonal is
color 5. Symmetric color-8 entries connect two objects with the same cell shape up
to rotation. Reflections are not accepted: in train 0 the unmatched five-cell
object is a reflected, rather than rotated, version of the matched pair.

Probe: I wrote a train-case assertion harness against `challenge.json`. The stub
failed with `NotImplementedError`, as expected. The first implementation then
failed because `_normalize` consumed a generator while taking the first minimum;
materializing the iterable fixed that implementation bug. The resulting solver
matches all three visible outputs exactly.

Implementation: split objects by same-color 4-connectivity, sort by bounding-box
top-left coordinate, canonicalize each shape over its four rotations, emit 5 on
the diagonal and symmetric 8 where canonical rotation signatures agree.

Remaining uncertainty: the examples do not directly distinguish same-color
objects that touch orthogonally, but treating such cells as one object is the
natural object segmentation and matches every visible case. Query predictions
are left to the blind checker/private scoring.
