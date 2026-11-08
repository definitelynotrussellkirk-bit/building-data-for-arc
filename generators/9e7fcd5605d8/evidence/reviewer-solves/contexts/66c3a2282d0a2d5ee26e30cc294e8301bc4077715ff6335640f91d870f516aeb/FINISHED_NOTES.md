# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Earlier exposure: none to this task's generator, rule, solutions, or notes. I only read the visible examples produced by `blind prepare`.

Hypothesis: each 4-connected nonzero object is classified by topology. Objects that enclose at least one orthogonally enclosed background cell become color 8; objects with no enclosed cell become color 4. This explains the hollow rectangles/rings and the two-hole 4x4 object, while open C/U shapes, solid blocks, and irregular open shapes become 4. Original nonzero color, area, and position are irrelevant.

Implementation probe: find 4-connected nonzero components. For each component, add a one-cell frame around its bounding box and flood all non-component cells reachable from that exterior frame. Any non-component cell left unreachable is a hole. Recolor the component 8 when at least one such cell exists, otherwise 4. Other components are treated as traversable space for this object-specific topology test.

Remaining uncertainty: unseen data could define components by same-color connectivity rather than all nonzero connectivity, but every visible object is monochrome and spatially separated. The current rule matches all visible examples under the simpler object interpretation.
