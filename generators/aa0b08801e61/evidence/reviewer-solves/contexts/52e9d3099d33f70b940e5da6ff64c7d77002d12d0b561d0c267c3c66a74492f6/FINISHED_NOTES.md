# Solve work log

This is a human-readable reasoning log for the post-repair visible-only solve. I had already seen the task rule while repairing the assigned generator, so this episode is **not blind** and will be finished with `earlier-exposure yes`. During this solve I did not reopen the generator, Racket rule, reference solution, private labels, or prior solution explanations; I used only the prepared visible examples.

## Revision 1 — component reflection classification

The output preserves the grid size and every nonzero object's occupied cells, but replaces the object's input color. The replacement cannot be a lookup by input color: the examples use arbitrary source colors, and the same geometric role appears under different colors.

I compared each 4-connected monochrome object's shape inside its tight bounding box:

- A plus or 2×2 square is invariant under both left-right and up-down reflection and becomes 8.
- The six-cell shape `010 / 111 / 101` is left-right symmetric but not up-down symmetric and becomes 2.
- The six-cell shape `110 / 011 / 110` is up-down symmetric but not left-right symmetric and becomes 3.
- The small bent/stair shapes lack both symmetries and become 4.

Hypothesis: find each same-color 4-connected component, normalize it to its tight bounding box, compare the mask with its horizontal and vertical reflections, and recolor all component cells using `(both, LR-only, UD-only, neither) -> (8, 2, 3, 4)`.

The implementation uses an independent flood fill and explicit set reflections. It constructs a fresh zero grid, so source colors cannot leak into the answer. No competing visible-example rule remains that explains the novel square/T/L shapes as consistently as reflection classification.
