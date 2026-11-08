# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Earlier exposure declaration

Before this visible-only episode I had already inspected the assigned generator and
canonical rule while repairing it, so this is an exposed post-repair solve. During
this episode I used only the prepared visible examples and did not reopen the
generator, Racket authority, reference solutions, or private labels.

## Revision 1 — largest-component column histogram

Across the three demonstrations there are three separated monochrome objects. The
output contains as many cyan cells as the largest object (10, 9, and 10 cells), and
its width equals that object's horizontal span. Reading each output column gives
the corresponding number of cells in the largest input object's column. The bars
are top-justified and recolored cyan (8). A wide but smaller left object in examples
1 and 2 rules out selecting by width or leftmost position.

Implementation: find same-color 4-connected components, select the greatest cell
count, count its cells by input column across the full bounding-box width, and draw
top-justified cyan bars. Remaining uncertainty is limited to unseen ties; every
visible lesson has a unique largest object.
