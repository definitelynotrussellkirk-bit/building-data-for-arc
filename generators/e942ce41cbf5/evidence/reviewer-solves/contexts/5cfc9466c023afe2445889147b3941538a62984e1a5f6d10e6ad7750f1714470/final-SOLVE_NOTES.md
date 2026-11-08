# Solve notes

## Hypothesis 1 — normalize the two masks and decode the corner controls

The blue cells form one small shape and the red cells form a second shape placed elsewhere only to keep them visually separate. I translated each shape so its minimum row and column are zero.

The bottom-left cell varies over 3, 4, and 6. Comparing the three visible outputs supports:

- 3: union of the normalized shapes
- 4: intersection
- 6: symmetric difference (xor)

The bottom-right cell varies over 7, 8, and 9. Comparing the red shape against each output supports:

- 7: identity
- 8: rotate the normalized red shape 90 degrees clockwise
- 9: reflect the normalized red shape horizontally

After transforming red and applying the operation, crop the resulting coordinates to their bounding box and recolor every occupied cell cyan (8). If an intersection is empty, return the visible convention of a 1×1 zero grid.

## Probe

I implemented that rule directly and checked it against all three visible examples. The key disambiguating probes are the 4/7 example (identity + intersection) and 6/8 example (clockwise rotation + xor); together with 3/9 they exercise all six dictionary entries once.

## Prior exposure disclosure

I had already inspected this task while improving its generator, so this is not a blind solve. During this solve phase I used only `solve/challenge.json` and did not consult the Racket rule, generator, reference solution, private labels, or prior solution text.
