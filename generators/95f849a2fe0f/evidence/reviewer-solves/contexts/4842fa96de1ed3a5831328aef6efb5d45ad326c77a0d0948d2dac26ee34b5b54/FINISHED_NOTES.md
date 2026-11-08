# Post-repair visible-only solve notes

## Prior exposure

I had already inspected and repaired this task's generator and canonical rule before this separate solve episode. I therefore cannot claim blindness. During this solve phase I used only the visible presentation produced by `solve_episode.py prepare`; I did not reopen the generator, canonical rule, private labels, prior solution text, or reference implementation.

## Visible-example reasoning

Each input contains exactly two four-cell connected objects, colors 2 and 3, placed far apart. Their absolute positions and source colors disappear in the output. Translating each object independently so that its own top-left occupied cell becomes coordinate `(0, 0)` explains all three examples.

At each coordinate in that shared local frame:

- a cell occupied by exactly one normalized object becomes cyan 8;
- a cell occupied by both objects cancels to 0;
- cells occupied by neither remain 0.

This is the symmetric difference (XOR) of the two normalized cell sets.

The output frame starts at the normalized origin `(0, 0)` and extends through the maximum row and column used by the XOR. It is **not** cropped again around the cyan cells. Train example 0 proves this because the only cyan cells are on the third row, while two all-zero rows are retained above them.

## Implementation

`solve()` extracts colors 2 and 3, normalizes each set independently, computes set XOR, allocates the shared-origin frame through the largest XOR coordinate, and paints the remaining cells 8. If the two normalized shapes are identical, it returns the authority-compatible `[[0]]` edge case.
