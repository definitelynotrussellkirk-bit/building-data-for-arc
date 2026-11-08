# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Prior exposure declaration

Before this solve I had already inspected the assigned generator and canonical rule while repairing it. This is therefore an exposed post-repair solve, not a blind solve. During this solve phase I consulted only `solve/challenge.json` and did not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1

Hypothesis from the three visible demonstrations: find each nonzero monochrome 4-connected component independently, compute its tight row/column bounding rectangle, and fill that rectangle with the component's color on an otherwise zero output. Repeated colors remain separate when disconnected; the second and third demonstrations visibly require this because two color-3 or color-9 objects occupy distant boxes.

Implementation probe: breadth-first component extraction by equal color and orthogonal adjacency, then rectangle painting. I chose a fresh zero canvas rather than copying the input because every visible output consists exactly of the filled component boxes. Remaining uncertainty is limited to whether diagonal contact should join objects; the examples and standard ARC object convention support 4-connectivity, and the visible repeated-color cases make color-global grouping untenable.
