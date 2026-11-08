# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observations

I had not seen the rule, generator, private labels, or any earlier explanation for task `8a2e39528187` before this solve. Each grid contains four 4-connected monochrome objects. Outputs preserve every occupied cell and replace each object's color with one of `2,4,6,8`.

Across the visible pairs, objects are ordered primarily by cell count: sizes 2, 3, 4, and 5 receive `2,4,6,8`. One example contains two size-2 dominoes; the one whose top-left occupied cell comes first in row-major order receives `2`, and the other receives `4`. Hypothesis: find 4-connected nonzero components, sort by `(cell_count, min_row, min_col)`, and recolor in that order with `2,4,6,8`.

I added a visible-example regression script before implementing the hypothesis. It should initially fail because `solve` is still the provided stub.

## Revision 1

Implemented the component-ranking hypothesis directly. Components use 4-connectivity and require a shared original color, preventing adjacent differently colored objects from merging. The visible regression now passes all four demonstrations. Remaining uncertainty is limited to the tie-break: only one demonstration exposes an equal-size tie, and it supports row-major order of each component's first occupied cell.
