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

## Revision 1 result and root-cause trace

The visible regression probe failed only on training example 3.  Object-level
instrumentation showed that every object still followed the hole invariant, but
the sole object with four enclosed regions was colored 7 rather than 4.  Counts
1, 2, and 3 map to the same-numbered colors; the observed codebook is therefore
`{1: 1, 2: 2, 3: 3, 4: 7}`.  Both masked test inputs contain one four-hole
object, so the exception is relevant rather than incidental.

The first checked revision intentionally remains recorded as a failed solve
(2/3 visible examples).  Revision 2 changes only the final hole-count-to-color
encoding and leaves component and topology logic unchanged.
