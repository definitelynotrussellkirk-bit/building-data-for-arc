# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: I had not opened this task's generator, canonical rule, reference
solution, private labels, or prior explanation. I used only the four visible pairs.

Hypothesis: the single non-gray colored cell is a direction instruction whose color
maps 1→left, 2→up, 3→right, 4→down. The entire gray (6) object moves exactly one
cell in that direction and the instruction cell disappears. Its geometric position
is irrelevant: examples 0–3 each isolate one marker color and one cardinal shift.

Implementation: identify the unique marker color in {1,2,3,4}, create a zero-filled
output of the same shape, and copy every gray cell at the corresponding one-cell
offset. Reject malformed or out-of-bounds cases rather than silently clipping.
