# Solve notes

## Exposure declaration

This is not a blind attempt. I reviewed the assigned generator and canonical task before this solve episode. After `solve prepare`, I did not reopen the generator, Racket rule, canonical labels, independent oracle, or previous solution explanations.

## Visible-example inference

All four demonstrations preserve every nonzero cell. The changed cells are exactly zeros lying strictly inside one or more monochrome rectangular outlines.

A zero inside only the outer outline takes the outer color. A zero also inside an inner outline takes the inner color. The three-level examples show the same rule recursively: choose the smallest enclosing rectangular outline, independent of numeric color order.

The implementation therefore:

1. finds same-color 4-connected components;
2. recognizes components that are exact rectangular borders at least 3 by 3;
3. orders those frames by bounding-box area, smallest first;
4. replaces each zero by the first frame that strictly contains it;
5. preserves zeros outside all frames and all original nonzero cells.

A 2-by-N colored terminal rectangle has no strict interior and need not act as a frame, matching what can be inferred from the visible transformations.
