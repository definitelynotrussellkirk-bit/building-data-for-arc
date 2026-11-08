# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure declaration

Before this visible-only solve I had already reviewed and repaired this task's generator and canonical rule, so this is an exposed post-repair solve, not a blind solve. After `solve prepare` I did not reopen the generator, Racket rule, reference solutions, private labels, or prior solution explanations.

## Revision 1 — component area ordering and gallery packing

Visible evidence: each input contains three isolated monochromatic nonzero components. The output preserves each component's color and exact cropped shape, orders the crops by increasing number of colored cells (3, then 4/5, then 5/8), aligns their bounding boxes at the top, and inserts exactly one all-zero column between adjacent crops. Absolute input positions disappear. The 5-cell versus 8-cell examples also distinguish cell count from bounding-box area.

Implementation: find same-color 4-connected components; crop each to its tight bounding box; sort by `(cell_count, top, left)` as a deterministic tie fallback; pack top-aligned with one zero column. Remaining uncertainty: the visible examples contain no equal-area tie, so the tie fallback is not identified by the presentation.
