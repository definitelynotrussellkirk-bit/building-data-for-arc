# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Earlier exposure: none to this task's generator, canonical rule, private labels, or prior solution explanation. I only read the visible challenge prepared in this directory.

Hypothesis: the full row of 9s separates a single template object above from several candidate objects below. The changed candidate is the unique 4-connected component with the same shape as the template after translation and any quarter-turn rotation; mirror reflection is not allowed. Evidence across the three examples:

- Example 0 selects the exact-orientation L tetromino and rejects its mirror and a T tetromino.
- Example 1 selects a 90-degree rotation of the five-cell template.
- Example 2 selects a 180-degree rotation while rejecting the mirror and an S tetromino.

Implementation: locate the all-9 separator row, collect the nonzero/non-9 template cells above it, enumerate four normalized rotations, split lower colored cells into 4-connected components, and recolor the first rotationally congruent component to 2. The grid otherwise remains unchanged.

Remaining uncertainty: the visible data contains one qualifying component per puzzle. If a hidden input contains multiple rotational matches, the examples do not establish whether all or only one should be recolored; I choose the first unique match implied by the demonstrations.
