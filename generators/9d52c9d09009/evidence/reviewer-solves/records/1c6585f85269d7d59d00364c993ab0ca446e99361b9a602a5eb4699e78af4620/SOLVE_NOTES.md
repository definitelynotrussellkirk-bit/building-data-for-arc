# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 hypothesis (before implementation)

The input contains several disjoint azure (8) shapes.  Each shape is recolored
uniformly.  Inspecting the visible examples as binary masks suggests the new
color is the number of enclosed 4-connected background regions inside that
shape: examples labeled 1 have one enclosed hole, labels 2 and 3 have two and
three holes, and the one label-7 object has seven separate enclosed holes.

Probe: I decomposed every visible input into 4-connected foreground components,
printed each bounding-box mask, and compared the count of internal background
components with the output color.  The correspondence held for every visible
object.  I will implement component discovery plus flood filling of background
from each component bounding-box boundary; unvisited background components are
holes.  Remaining uncertainty: whether diagonal contact should merge holes.  The
visible masks support 4-connectivity, matching standard ARC object connectivity.
