# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: yes. I repaired this generator before entering the solve lane, so this is not a blind solve. During this lane I kept the generator, Racket authority, reference solutions, private labels, and earlier solution explanations closed.

Visible-example hypothesis: identify the modal colour as background and the 4-connected non-background compounds. Each compound contains two vertically stacked colour classes. Repaint onto a fresh background canvas, moving the upper class one column left and the lower class one column right.

Evidence from the visible pairs:
- Train 0 shows the same local upper-left/lower-right motion on two separate compounds.
- Train 1 shows that shape and size are preserved while only horizontal position changes.
- Train 2 is the decisive probe: colour 4 is lower in the right compound but upper in the left compound, so direction is determined by each compound's vertical role, not by a global colour lookup.

Implementation choice: use 4-connected components, group cells by colour inside each component, sort the two colour classes by their minimum row, and write shifted cells to a fresh modal-background grid. Remaining uncertainty is limited to out-of-domain inputs with other than two colours per compound; the visible challenge does not show those.
