# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

I observed that each example contains one uncommon shape left gray (5) and two or three translated copies of another shape recolored blue (1). I tested object connectivity mentally against training example 3: the two diagonal gray cells must form one 8-connected two-cell object. With 4-connect they would be two identical singleton objects and should have changed, which contradicts the example.

Implemented translation-normalized signatures for 8-connected non-background components. Any signature occurring more than once is recolored to 1; unique shapes retain their original color. This predicts that test 1 recolors the two 3x3 squares but not the L-tromino, and test 2 recolors the two 2x2 squares but not the horizontal domino.

No reference material, generator source, private labels, or prior explanation was consulted.
