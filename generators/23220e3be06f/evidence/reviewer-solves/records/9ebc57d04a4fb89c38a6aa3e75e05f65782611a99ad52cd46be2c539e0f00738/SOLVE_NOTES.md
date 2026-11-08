# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — crop and marker-directed reflection

Earlier exposure before this solve: none to this task's rule, generator, private
labels, or prior solution explanations. I only read the public presentation
created by `python3 review.py blind prepare`.

Hypothesis: the isolated nonzero cell at `(0, 0)` is an operation code and is not
part of the output object. The remaining nonzero cells define a tight bounding
box. In both visible examples with marker `5`, the output is the tight crop
reflected left-to-right. In the visible example with marker `6`, the output is
the tight crop reflected top-to-bottom. I compared every cell of each proposed
crop and reflection against all three visible outputs; no rotation or color
replacement is needed.

Implementation: exclude `(0, 0)`, crop to the bounding box of all other nonzero
cells, apply a horizontal reflection for `5` and a vertical reflection for `6`.
The remaining uncertainty is whether unseen marker values exist, but both query
markers are among the two demonstrated values, so the solution rejects any
unsupported marker rather than guessing.
