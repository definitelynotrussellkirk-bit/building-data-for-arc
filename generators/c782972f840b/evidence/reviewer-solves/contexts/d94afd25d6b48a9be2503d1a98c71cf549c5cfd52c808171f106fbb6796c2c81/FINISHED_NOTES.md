# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — pairwise object relation matrix

Earlier task-specific rule exposure: none. I had only read the packet's general
review instructions and generic ARC design guidance before this solve; I did not
open this task's generator, canonical rule, notes, private labels, or prior solve.

Visible observations:

- The output side length equals the number of nonzero monochrome 4-connected
  objects, ordered by row-major discovery of their first cell.
- Every diagonal is 9, so each row/column represents one input object.
- Off-diagonal values decompose additively: 2 means equal source color, 4 means
  equal binary shape up to 90-degree rotations, 6 means both, and 0 means neither.
- Reflections do not count as the shape relation. In train 2, the first three L
  tetrominoes are rotations of one another while the fourth is the mirrored
  chirality, matching the 4/6 versus 0 entries.

Probe: I wrote `WORK/checks/blind-solve-visible-test.py` before implementation.
It checks all three visible training pairs and a small synthetic case where both
relations hold. The initial run failed at the template's `NotImplementedError`
and is retained in `WORK/checks/blind-solve-visible-test.red.log`.

Implementation: extract same-color 4-connected components, normalize each to a
binary bounding box, canonicalize over four rotations only, then build the
symmetric matrix. Remaining uncertainty is limited to inputs outside the visible
contract (for example, diagonally connected cells); the examples consistently
support 4-connectivity and background color 0.
