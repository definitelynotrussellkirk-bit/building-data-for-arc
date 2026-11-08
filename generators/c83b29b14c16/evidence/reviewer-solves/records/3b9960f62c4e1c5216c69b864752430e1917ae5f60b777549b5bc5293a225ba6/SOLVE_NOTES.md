# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — axis-aligned pairs occurring exactly twice

Before this blind episode I had not opened task c83b29b14c16's generator, rule,
notes, solutions, audit records, or private labels. I had only read the packet's
general instructions and AGENTS.md.

Visible-example hypothesis: group nonzero cells by color. A color is extended only
when it appears exactly twice and the two cells share a row or a column. Fill the
background cells on the inclusive segment between those endpoints. Leave singleton
colors, colors appearing three or more times, and diagonal pairs unchanged.

Evidence from the examples: the three 8 cells in training example 3 remain
unconnected despite sharing a column, while every aligned exactly-two pair is
filled and the diagonal 4 pair in example 2 is unchanged. The implementation
preserves any differently colored nonzero cell if an unobserved crossing occurs;
the visible examples do not constrain crossing behavior.

No earlier failed implementation exists; this is the first genuine solve attempt.
