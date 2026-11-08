# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — closed-frame membership

Observed that every input contains one or more complete axis-aligned rectangles
outlined in color 1, plus color-2 markers. In all three demonstrations, a 2
strictly inside a 1-outline changes to 4; every 2 outside all outlines remains 2.
This also explains markers at different interior positions and multiple frame
sizes without relying on a fixed coordinate, rectangle count, or marker count.

Implemented 4-connected color-1 component discovery, validated each component as
a complete rectangular border, and recolored only 2-cells strictly inside at
least one validated border. Remaining uncertainty: whether production examples
may use touching/nested frames whose outlines form one connected component; the
visible lesson does not require that extension, and the current rule is the
smallest hypothesis fitting every shown pair.
