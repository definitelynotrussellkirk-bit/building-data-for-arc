# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

From the visible pairs, row 0 acts as a per-column legend and is cleared. For
each later row, zeros remain zero; every non-zero cell is replaced by the
header value at the same column. If that header value is zero, the body cell is
erased. Example 1 shows both 7 and non-7 body values taking header colors, and
examples 2–3 show off-legend values of multiple colors disappearing, ruling
out body-color-conditioned erasure.
