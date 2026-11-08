# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Visible-example hypothesis: treat each non-zero same-color 4-connected component
as an object, select the component with the greatest cell count, and return its
tight crop without rotating or recoloring it.  This explains training examples
0 and 1 directly.  Training example 2 contains two six-cell components; the
shown answer is the earlier one in row-major order, so I use top/left reading
order as the deterministic tie break.  The first test query has another equal
six-cell tie in the same row, making the leftmost tie break a real prediction
rather than an unused implementation detail.

Alternatives considered from the visible data included maximum bounding-box
extent and selecting a fixed six-cell polyomino.  Maximum cell count is simpler
and explains the smaller distractors and the split same-color distractor in
training example 1.  Remaining uncertainty is whether ties are intentionally
reading-order based or use an unobserved shape property.
