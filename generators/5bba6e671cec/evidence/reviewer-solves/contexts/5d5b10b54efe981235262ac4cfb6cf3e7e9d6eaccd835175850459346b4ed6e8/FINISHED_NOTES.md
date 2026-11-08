# Visible-only solve notes

Human work log. I had already studied this task while repairing its generator, so this is an exposed solve rather than a blind one. During this solve episode I used only `solve/challenge.json` and did not reopen the generator, Racket rule, solutions, or private labels.

## Hypothesis from the three demonstrations

- Colors 4 and 7 form a fixed scaffold: every 4/7 cell is unchanged.
- Every other color is treated globally, even if its cells are disconnected. The first and third demonstrations each have three such colors and cyclically relabel the three regions; the two-color demonstration swaps its two non-frame colors.
- The cycle is geometric rather than numeric. Compute each non-frame color's whole-color centroid around the grid center, order centroids clockwise (north = angle 0), and move each color into the next clockwise region. Equivalently, at cells currently carrying color `c_i`, write the previous color in the clockwise ordering.
- Color 0 is an ordinary region, not background: in demonstrations 1 and 3 its cells are recolored and another region becomes 0.

## Implementation plan

Collect all colors except 4 and 7; compute mean row/column for each; sort with `atan2(dx, -dy)` modulo one turn; create the one-step cyclic mapping; preserve 4/7 exactly. This also handles the first test's disconnected color-2 cells because the centroid is over all cells of that color.

No failed natural revision was needed; I am submitting the direct rule inferred from the visible examples.
