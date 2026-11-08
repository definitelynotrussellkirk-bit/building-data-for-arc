# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Earlier exposure declaration

Before this visible-only episode I had already inspected and repaired this task's generator and had seen the canonical Racket rule. I therefore cannot claim a blind inference. During this solve episode I did not reopen the generator, Racket rule, reference solutions, or private query labels; I used only the prepared visible examples.

## Revision 1 — area cue, monochrome objects, 2× crop

The examples suggest that row 0 is a size key: the number of color-1 cells is 4, 4, and 3 respectively. In each body there is exactly one monochrome 4-connected object with that many cells. The output is the selected object's bounding-box crop from the original grid, with every cell doubled horizontally and vertically; zeros inside the bounding box are preserved. Example 1 also contains a non-1 header cell, so I count only color 1 rather than every nonzero header cell. Example 2 has differently colored objects touching at an edge, so components must be color-sensitive.

I implemented that rule directly. Remaining uncertainty before checking: none in the visible demonstrations; I expect the query objects of sizes 4 and 3 to be selected and scaled the same way.
