# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none to this task's generator, rule, notes, solutions, or labels. I inspected only the visible challenge.

Observation: each training input contains several monochrome objects. The output is exactly one object's cropped binary shape, with every occupied cell recolored 8. In all three examples the selected object's bounding box has the greatest width: widths 7, 7, and 5 respectively. This distinguishes it from alternatives such as largest area, rarest color, or first object in reading order.

Hypothesis: split the nonzero grid into 4-connected same-color components, select the component with the widest bounding box, crop to that box, and emit 8 for its cells and 0 elsewhere. I used area only as a deterministic tie-breaker; the visible examples have no width tie. A local regression against all visible training pairs is the first probe.

Official visible-only check: 3/3 training pairs passed. I stopped after the first genuine hypothesis because it explains every visible example and produces unambiguous predictions for both masked queries. Remaining uncertainty is only the unobserved width-tie policy; no test instance appears tied.
