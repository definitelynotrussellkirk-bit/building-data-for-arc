# Solve work log

## Exposure declaration before solving

I had already inspected and repaired this task's generator and had seen the task rule before this required post-repair episode. This is therefore an **exposed post-repair solve**, not a blind solve. During this solve phase I consulted only `solve/challenge.json`, this work log/template, and my own Python solution; I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Revision 1 — tight mask crop, palette-order recoloring, one-column gaps

Visible-example observations:

- The nonzero cells of row 0 form a palette. Their physical columns disappear from the output; only their left-to-right order remains.
- The color-1 cells below row 0 define a binary mask. Each output has the mask's tight bounding-box height and repeats its tight width once per palette entry.
- Every repeat replaces 1 with its corresponding palette color and preserves zero holes.
- Consecutive copies are separated by exactly one all-zero column.
- The third training example is especially discriminating: its palette is `[7, 4]`, and the output keeps `7` before `4`, so numeric sorting is wrong.
- The three training masks have tight shapes 3x3, 2x3, and 3x3. Their outputs have widths `2*3+1`, confirming the single-gap formula rather than concatenation or retention of original canvas spacing.

Implemented `solve(grid)` by reading nonzeros from row 0, finding all color-1 coordinates, normalizing them to the tight mask bounding box, allocating width `n_palette * mask_width + (n_palette - 1)`, and painting one recolored copy at offsets `i * (mask_width + 1)`.

Alternatives rejected from the visible examples: sorting colors numerically; always forcing a 3x3 tile; filling the mask bounding box solid; preserving the palette's original horizontal distances; using no gap; or returning the original canvas with additions.

Predicted test outputs before checking:

- Test 0: a 3x4 diagonal-band mask, first in color 2 and then color 3, separated by one blank column (3x9 output).
- Test 1: a 3x3 six-cell mask in colors 2, 3, 4, 7 in that order, with one blank column between copies (3x15 output).

Remaining uncertainty is limited to malformed inputs outside the visible lesson grammar; the implementation raises on a missing palette/mask or ragged grid rather than inventing behavior.
