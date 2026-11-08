# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — connected stamp hypothesis

Before implementation I inspected only the visible examples produced by `blind prepare`.
Each example contains one 4-connected multicolor component and several isolated or
monochrome cells.  The multicolor component is a reusable stamp: its most frequent
color draws the body, while two singleton colors decorate it.  Of the singleton
colors, one occurs more than once outside the component and acts as the anchor.
The other singleton color has one stray occurrence that is not copied and disappears.

Probe: translate the complete component so its anchor overlays every occurrence of
the anchor color, including the anchor inside the original component.  Superimpose
all translated copies on a blank grid.  Equal colors merge; unequal nonzero colors
become 9.  This exactly accounts for all three visible outputs, including the three
9 cells in example 0 and both 9 cells in examples 1 and 2.  The implementation uses
4-connectivity, chooses the component with the most distinct colors, and chooses the
singleton prototype color with the greatest number of occurrences outside it.

Remaining uncertainty: the visible examples do not show a stamp crossing a grid
boundary or a tie in outside singleton counts.  The program clips translated cells
to the grid and uses occurrence count as the deterministic tie-breaker.
