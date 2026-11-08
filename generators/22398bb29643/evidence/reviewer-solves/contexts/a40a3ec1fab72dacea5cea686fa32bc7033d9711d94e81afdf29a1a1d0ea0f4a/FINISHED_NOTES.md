# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — component colors in top/left order

I had earlier exposure to the intended rule while repairing this generator, but during this solve I did not reopen the generator, Racket source, reference outputs, private labels, or earlier solution explanations. I used the visible examples above.

Every nonzero figure is a separated monochrome 4-connected component. The output has one cell per component, preserving duplicate colors: training example 1 has two separate color-2 components and outputs color 2 twice. Components are ordered by the top row of their bounding box, with the left column as the tie-breaker. This explains `[2, 8, 9, 1, 6]` in example 0, the two same-row top components in example 1, and `[7, 6, 2]` in example 2.

I implemented a nonzero 4-neighbor flood fill, sorted components by `(minimum row, minimum column)`, and emitted the color at each component's row-major first cell. A same-color-only flood fill is indistinguishable on the visible monochrome components, so I retained the simpler object interpretation: touching nonzero cells form one object. The visible test predictions are query 0 → `[7, 2, 2]` and query 1 → `[7, 8, 2]`.
