# Visible-only solve log: e69a3b575440

This is the exposed post-repair solve. I had already inspected the generator and canonical authority before this solve episode, so the record is **not blind**. After `solve_episode.py prepare`, I used only the displayed public examples and did not reopen the generator, Racket rule, reference solution, private labels, or census.

## Hypothesis

The nonzero value in the top-left corner is a command token, not part of the object. Replace it with background 0, crop to the bounding box of the remaining nonzero cells, then transform that crop according to the command.

The eight demonstrations directly support this table:

- 1: unchanged crop
- 2: rotate 90 degrees clockwise
- 3: rotate 180 degrees
- 4: transpose
- 5: reflect left/right
- 6: reflect up/down
- 7: transpose (same visible operation as 4)
- 8: anti-transpose, equivalent to transpose followed by 180-degree rotation

I checked each mapping by manually comparing the cropped input object with the displayed output, paying particular attention to asymmetric shapes and multi-color orientation. The query command tokens are 1 and 2, both explicitly demonstrated. The first implementation encodes the full displayed table rather than special-casing the queries.
