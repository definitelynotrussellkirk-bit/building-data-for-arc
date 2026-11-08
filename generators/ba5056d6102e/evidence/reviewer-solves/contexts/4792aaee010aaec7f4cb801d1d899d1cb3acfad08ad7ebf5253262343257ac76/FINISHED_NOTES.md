# Solve notes

This is a human work log from the visible `solve/challenge.json` only. I had earlier rule exposure during the generator review, so this is not a blind solve; I did not consult the generator, Racket source, reference solution, private labels, or prior explanations during this solve phase.

## Visible-example analysis

All three demonstrations contain one full-width row of color 5. It splits the input into equal-height top and bottom panels with matching dimensions. The output has the size of one panel and uses only 0 and 8.

Coordinate checks support a Boolean intersection rule:

- Where both aligned panel cells are nonzero, the output is 8.
- Where only the top cell, only the bottom cell, or neither cell is nonzero, the output is 0.
- Foreground identities vary across examples (2/3, 4/6, 6/2), so the operation depends on occupancy rather than literal colors.

I rejected union, xor, top-only, bottom-only, and literal-color matching because the visible demonstrations contain counterexamples to each.

## Implementation

`solve/solution.py` locates the unique full color-5 divider, checks that the panels have equal height, and emits 8 exactly at aligned coordinates where both cells are nonzero.

No revision was needed before the first execution check.
