# Post-repair visible-example solve notes

This is a human work log based only on `solve/challenge.json` during the solve phase.
I had earlier exposure to the task family while repairing the assigned generator, so this is not a blind solve; I did not consult the generator, Racket source, private labels, or a reference solution while writing this episode.

## Hypothesis

All nonzero input cells are blue (`1`) and form separate rectangular outlines nested from outside to inside. The output preserves their locations and changes the outermost outline to `2`, the next outline to `3`, then `4`, `5`, and so on. Background stays `0`.

The visible examples support this across two, three, and four outlines, including off-center and non-square layouts. Because blank moats disconnect adjacent outlines, four-connected components recover the frames directly. I rank those components by bounding-box area from largest to smallest, which matches containment depth on every visible example.

## Implementation

1. Find four-connected components of color `1`.
2. Compute each component's bounding-box area.
3. Sort descending and recolor component rank `0,1,...` as `2,3,...`.
4. Leave every other cell `0`.

No revision was needed before the first visible-example check.
