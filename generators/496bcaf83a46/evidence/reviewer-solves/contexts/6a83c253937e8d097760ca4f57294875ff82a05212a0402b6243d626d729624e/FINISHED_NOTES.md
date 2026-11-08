# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — maximum marker count

Earlier exposure: none to this task's generator, rule, notes, solutions, or private labels. I had only read the packet-level instructions before preparation.

Hypothesis from the three visible pairs: each non-gray color forms a rectangular frame. Color 8 is a marker/noise color. Count gray cells strictly inside every non-gray frame, erase all gray cells, and fill the complete bounding rectangle for every frame tied for the largest marker count. Leave the other frames hollow. This explains the tie in train 0 (both 4-marker frames fill), the unique 2-marker winner in train 1, and the unique 3-marker winner in train 2. The all-gray rectangular decoy in train 2 disappears because gray is globally erased rather than treated as a candidate frame.

Implementation probe: find 4-connected components of each color except 0 and 8, require each component to contain a full rectangular perimeter, count interior 8s in the original grid, erase every 8, then fill all maximum-count rectangles. Remaining uncertainty: the examples do not show nested/overlapping frames or multiple same-color frames touching each other; the component/perimeter formulation handles separate same-color frames but not touching ones as distinct objects.
