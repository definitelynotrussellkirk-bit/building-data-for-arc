# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure declaration before revision 1

I had already inspected and repaired this task's generator and selected rule before
this required post-repair solve, so this is **not blind**.  During the solve phase I
used only the displayed challenge and did not reopen the generator, Racket source,
private labels, or earlier solution explanations.

## Revision 1

Hypothesis from the three visible pairs: treat each nonzero 4-connected component
independently.  Its original cells become zero; every in-bounds zero cell sharing
an edge with any component cell receives that component's color.  Diagonal
neighbors are not colored.  The ring in train example 0 is decisive: the enclosed
center is colored too, so the operation is based on local orthogonal contact, not
only exterior background.  Train example 2 confirms a two-cell domino gets a
six-cell shell.

Implementation: flood-fill same-color components, start from an all-zero output,
and write every original-zero cardinal neighbor of each component.  I preserved
input dimensions and did not mutate the input.  The generated examples appear to
keep shells disjoint; overlapping-shell tie behavior is therefore not inferred.
