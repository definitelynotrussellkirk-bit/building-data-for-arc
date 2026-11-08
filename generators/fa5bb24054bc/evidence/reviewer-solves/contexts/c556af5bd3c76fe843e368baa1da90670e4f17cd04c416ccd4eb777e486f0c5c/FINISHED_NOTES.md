# Solve work log

## Prior exposure

This post-repair solve is **not blind**. Earlier in the same review I inspected and repaired the assigned generator and therefore had prior exposure to the task family and its intended relation. I did not reopen the generator, Racket rule, canonical reference, private labels, or earlier solution artifacts during this solve episode. The implementation below was reconstructed from `challenge.json` and is reported with `--earlier-exposure yes`.

## Visible-example observations

Each input consists of two to four colored shapes separated by entirely blank columns. Every output is a square matrix whose side length equals the number of shapes. The diagonal is always `5`, and the matrix is symmetric.

For the first training example:

- panel 1 has area 8 and one enclosed hole;
- panel 2 has area 4 and no hole;
- panel 3 has area 8 and no hole.

The corresponding off-diagonal labels distinguish all three comparisons:

- neither feature equal: `0` (panels 1 and 2),
- area equal only: `2` (panels 1 and 3),
- hole count equal only: `3` (panels 2 and 3).

The remaining examples contain pairs with both features equal, labeled `6`, and repeat the other relations in different sizes and positions. This explains every visible matrix entry with one rule.

## Implemented hypothesis

1. Split the grid at all-zero columns and tightly crop each resulting panel.
2. For each panel compute:
   - area = number of nonzero cells;
   - holes = number of enclosed 4-connected zero components.
3. Produce a pairwise relation matrix:
   - diagonal: `5`;
   - same area and same hole count: `6`;
   - same area only: `2`;
   - same hole count only: `3`;
   - neither: `0`.

The hole counter pads each cropped panel with a zero border, flood-fills exterior background, then counts the remaining zero components. The implementation is generic in grid height, panel count, colors, and shape dimensions.

## Revisions and uncertainty

This was the first implementation submitted in the post-repair episode. No alternative hypothesis or failed revision was needed because the first visible example supplies labels `0`, `2`, and `3`, while later examples visibly supply `6`. Remaining uncertainty is limited to private examples containing structures outside the displayed separator-and-shape grammar; the code deliberately avoids hard-coded dimensions or colors.
