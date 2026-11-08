# Exposed post-repair solve work log

This is a human-authored work log for the required post-repair episode. I had already reviewed the selected generator and canonical rule before this episode, so this is **not blind**. During the solve phase itself I used only the visible examples printed by `solve_episode.py prepare`; I did not reopen the generator, Racket source, reference solutions, or private labels.

## Hypothesis from the visible examples

The input has one object made of color 5 and isolated cells of other nonzero colors. Take the bounding box of all 5-cells and express each 5-cell as an offset from the bounding-box top-left, including cases where that top-left coordinate itself is empty. Clear the whole grid. For every nonzero non-5 cell at `(r,c)` with color `k`, paint the same offsets from `(r,c)` in color `k`, clipping only if an offset would leave the grid.

Evidence from the examples:

- Example 0 uses offsets `(0,0),(0,1),(0,2),(1,1)` and reproduces them at colors 7 and 2 while removing the source.
- Example 1 is decisive for bounding-box origin: its 5-cells have offsets `(0,1),(1,0),(1,1)`, so the first row-major 5-cell is not the origin. The colored outputs are shifted according to the empty bounding-box corner, not according to that first 5-cell.
- Examples 2 and 3 show five-cell and four-cell masks, multiple colors, source removal, and recoloring.

I will implement this rule directly in one revision. The two masked queries should be handled by the same extraction and stamping logic.
