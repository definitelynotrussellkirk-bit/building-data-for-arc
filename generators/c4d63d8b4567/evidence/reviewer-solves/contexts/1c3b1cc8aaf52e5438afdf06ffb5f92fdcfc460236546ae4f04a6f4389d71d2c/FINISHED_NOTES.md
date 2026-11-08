# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — unobstructed same-colour segments

Observed that outputs connect equal nonzero cells when they share a row or column,
filling only the cells between them.  The second training example distinguishes
simple alignment from *unobstructed* alignment: the vertical pair of 7s is not
joined because a 2 lies between them, while the horizontal 2 pair is joined.
The third and fourth examples also leave non-collinear outliers unchanged.

Implemented a general solver that groups original markers by colour, then by row
and column.  It joins adjacent original endpoints only when the complete interval
contains background or that endpoint colour, never overwriting another colour.
Endpoint selection is based on the original grid so a newly drawn segment cannot
create a new accidental pair.  Remaining uncertainty: a query containing two
valid differently coloured segments that cross on one background cell would be
ambiguous; none of the visible examples establishes a crossing convention.
