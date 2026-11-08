# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Prior exposure

Before this solve I had already reviewed this task's generator and canonical rule as part of the assigned repair, so this is an exposed post-repair solve, not a blind solve. During this solve phase I consulted only `solve/challenge.json`, this work log, my Python solution, and visible check feedback; I did not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1 — connectivity fill

Visible examples show color 5 acting as fixed walls. Within each 4-connected component of cells whose value is not 5, there is one nonzero colored cell. The output preserves every 5 and replaces all other cells in that connected component with the component's seed color. The second training example is decisive because a hole in a horizontal wall joins cells that would be separate rectangles; the color 9 fills through the opening, so the unit is 4-connected reachability rather than a rectangular bounding box.

I implemented a row-major flood fill over non-5 cells, collected each region's seed, and painted a fresh output initialized with walls. The visible data contain one seed per region. I left a defensive zero result for a seedless region rather than inventing a color, although such a region is not supported by the visible examples.

## Stop decision

Revision 1 passed all three visible training examples. I stopped because the opening-containing example directly distinguishes the implemented connectivity rule from the strongest simple rectangle rival, and no visible failure justified another revision. Masked query correctness remains withheld by the review protocol.
