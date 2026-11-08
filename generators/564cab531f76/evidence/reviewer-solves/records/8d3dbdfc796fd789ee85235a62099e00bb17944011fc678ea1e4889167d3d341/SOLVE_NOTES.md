# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Prior exposure declaration

Before this visible-only episode I had already reviewed the assigned task's generator and authority while repairing it, so this is **not blind**. During this episode I used only `solve/challenge.json` and my own Python implementation; I did not reopen the generator, authority, reference solutions, or private labels.

## Revision 1 — bounding-box-center nearest corner

Observed across the four visible pairs:

- The four nonzero corner cells are preserved and act as color markers.
- Every other same-color 4-connected object keeps its pixels but changes color.
- Objects in different quadrants take the corresponding corner color.
- Train pair 0 separates a component-level rule from a per-color global rule: the singleton objects independently map NW, SW, and SE, while the larger central object maps NE.
- The tall example places a four-cell object across the canvas middle. Its output is the southwest marker, suggesting the decision uses the object's extent rather than only its first pixel.
- The two 6×6 examples support comparing the center of each object's tight bounding box with the canvas center. Exact midpoint comparisons appear to prefer top and then left.

Implemented 4-connected components by color, excluded singleton corner components, compared doubled bounding-box centers to `(height-1, width-1)`, and recolored every component from the selected corner. The remaining uncertainty is only masked-query correctness; no alternative visible-example-consistent rule looked more natural than the bounding-box-center rule.
