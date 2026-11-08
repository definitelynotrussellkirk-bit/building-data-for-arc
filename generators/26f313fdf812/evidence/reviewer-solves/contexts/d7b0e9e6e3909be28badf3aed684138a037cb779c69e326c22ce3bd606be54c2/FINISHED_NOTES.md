# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial hypothesis
The nonzero cells form one monochrome object per color.  The output is an
object-by-object comparison table: diagonal/equal-area entries are color 1,
row-object larger than column-object is color 2, and smaller is color 3.
Objects are ordered by the top-left position of each 4-connected nonzero
component; when two colors touch inside one component, the larger/main color
comes before the smaller attached color.  This explains the otherwise reversed
orders of colors 3/6 in train 1 and 2/9 in train 3.

Planned probe: encode that rule and require exact agreement on all four visible
training pairs.  Remaining uncertainty is whether a multi-color component could
contain tied areas; no visible example does, so I will use first pixel position
as a deterministic tie-break after descending area.

## Revision 1 result
The implementation passed all 4/4 visible training examples in the official
visible-only checker.  I stopped after this single successful revision because
the examples jointly determine both comparison colors and the special ordering
of touching marker colors.  The private query labels remain unknown.  The only
material extrapolation is the deterministic tie-break for equally sized colors
inside one touching component; no visible case exercises that situation.
