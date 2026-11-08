# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: yes — I had already inspected the assigned generator during the
repair phase. During this solve I used only the prepared visible examples and did
not reopen the generator, Racket rule, reference output, or prior explanations.

Hypothesis from the visible examples: split the nonzero input into 4-connected
objects, normalize each object's occupied coordinates by translation only, and
count exact shape signatures. Recolour every object in a repeated exact-shape
class with 1; recolour a shape that appears only once with 2. Rotations and
reflections do not merge: example 2's two four-cell corner shapes are congruent
under a rotation but receive 2, while the two identically oriented T-like shapes
receive 1.

The implementation therefore preserves only object occupancy, not the original
foreground colour, and leaves background cells at 0. Remaining uncertainty is
limited to connectivity conventions; all visible examples support 4-connectivity.
