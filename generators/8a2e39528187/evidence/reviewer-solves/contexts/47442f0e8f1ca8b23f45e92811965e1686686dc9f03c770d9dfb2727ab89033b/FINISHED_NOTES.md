# Solve notes

This is a human work log based only on `challenge.json`. I had earlier exposure to the task rule while reviewing the generator, so this is not claimed as a blind discovery; I did not consult the generator, Racket source, reference solution, or private labels during this solve phase.

## Visible-example observations

- Every input has four spatial objects on color-0 background, and output preserves each object's exact cells while replacing its color.
- In training example 1, object areas are 2, 3, 4, and 5. Their output colors are respectively 2, 4, 6, and 8, independent of input color and position.
- Training example 3 contains a deliberate contact between a color-5 vertical object and a color-3 vertical domino. They remain separate objects, so connectivity is monochromatic 4-connectivity rather than color-blind nonzero connectivity.
- Training example 4 has objects whose input colors already come from {2,4,6,8}, but the output still follows area rank rather than preserving or numerically sorting input colors.
- When areas tie, the visible examples are consistent with lexicographic bounding-box order (topmost, then leftmost, then lower bbox coordinates) after area.

## Implemented hypothesis

Find monochromatic nonzero 4-connected components. Sort by `(number of cells, bounding box)` ascending. Paint the first through fourth components with `2, 4, 6, 8` on a blank grid, preserving geometry.

I implemented that hypothesis directly. No deliberate wrong attempt was created because the visible demonstrations already distinguish the plausible color-blind, input-color, and scan-order shortcuts.
