# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observations and hypothesis

Earlier exposure to this task's rule: none known. I used only the visible examples.
Each input contains one red (2) object and one green (3) object. After cropping each
object to its own tight bounding box and aligning those boxes at their top-left,
the output marks the symmetric difference of their occupied cells in azure (8),
then tight-crops that difference. Example 1 gives the uncropped 3x3 XOR directly;
examples 0 and 2 require the final crop.

Before implementing, I ran the packet checker against the untouched starter to
confirm that an absent solver is detected rather than silently accepted.
