# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observation (visible examples only)

I had not opened any generator, Racket rule, reference solution, private label, or prior solution explanation for this task.

Hypothesis: split every nonzero color into **4-connected monochromatic components**. A component survives only when it fills its axis-aligned bounding box exactly (a solid rectangle). Replace each surviving rectangle by the distinct cells at its bounding-box corners; erase every other component. This explains the removed notched/ring components, the unchanged 2x2 rectangle, ordinary rectangle corners, singleton cells, and one-cell-wide lines whose duplicate corners collapse to endpoints.

Key ambiguity to preserve in the implementation: components of the same color that touch only diagonally must remain separate. The first test query contains such a configuration, so 8-connectivity would wrongly merge lawful rectangles.

## Revision 2

Implemented the hypothesis directly with a four-neighbor flood fill. For each component I compare its cardinality with its bounding-box area; equality is sufficient because every component cell lies inside that box. Lawful components emit the set of four corner coordinates so degenerate rectangles naturally become a singleton or two endpoints.
