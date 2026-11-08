# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — rank the color-8 objects by bounding-box area

Earlier exposure: none to this task's generator, rule, private labels, or prior
solutions. I used only the visible examples from `blind prepare` and the public
challenge file.

Each input contains one or more 4-connected color-8 hollow rectangles (a
one-row or one-column innermost object is allowed). The output preserves every
occupied cell but replaces the object colors according to descending bounding-
box area: largest -> 2, second -> 4, third -> 6, fourth -> 7. This explains both
presentations: nested rectangles are separate components because a zero moat
separates them, while the disjoint examples independently establish the same
size ranking. For example, the 5x7 frame outranks the 8x4 frame by bbox area
35 > 32 and receives 2 rather than 4.

The first query has four nested components, so they should receive 2, 4, 6,
and 7 from outside inward. The second has three, receiving 2, 4, and 6.
Remaining uncertainty is only how a hypothetical equal-area tie should be
handled; no visible pair requires one. I use top row then left column solely as
a deterministic fallback.
