# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none to this task's generator, rule, notes, solutions, or labels.
I inspected only `challenge.json`.

Hypothesis: every nonzero input cell emits a full horizontal and vertical line
in its own color. A location covered by lines of exactly one distinct color gets
that color. A crossing of different colors becomes 2. Same-colored crosses merge
without changing color. Evidence: the first example has four differently colored
points and color 2 exactly at pairwise row/column intersections; the second has
two 6 points, and their mutual crossings remain 6 while crossings with 9 are 2.

Implementation: collect the set of source colors present in each row and column;
for each output cell, union those sets, returning 0 / the sole color / 2 according
to the number of distinct contributors. This also covers multiple sources in one
row or column without assuming one point per line.

Remaining uncertainty: whether 2 could also be an ordinary source color. The
visible examples consistently use it as the collision marker; the set-union rule
would still preserve a lone input 2 and mark mixed-color intersections as 2.
