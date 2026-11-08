# Blind solve notes — c2cd365ed4fa

## Initial observations

- Every training output is a 4×5 grid with background color 7.
- The five output columns have a stable color identity: `[5, 2, 8, 9, 6]`.
- Within a column, colored cells form a bottom-aligned vertical bar.
- The bar height is not the total number of input cells of that color. It matches the number of spatially separate monochromatic groups when diagonal contact counts as connected.

## Hypothesis

For each color in fixed column order `[5, 2, 8, 9, 6]`, count its 8-connected components in the input. Draw that many cells upward from the bottom of its output column in a 4×5 background-7 grid.

Evidence from the visible examples:

- Example 1: component counts are `5→1, 2→4, 8→2, 9→2, 6→0`, matching bar heights `[1,4,2,2,0]`.
- Example 2: counts are `5→1, 2→0, 8→4, 9→3, 6→2`, matching `[1,0,4,3,2]`.
- Example 3: counts are `5→4, 2→2, 8→1, 9→0, 6→2`, matching `[4,2,1,0,2]`.
- Diagonal connectivity is essential: several same-color shapes that would split under 4-connectivity form one group under 8-connectivity.

## Predicted test summaries

- Test 1 counts: `[2,0,1,4,1]`.
- Test 2 counts: `[0,1,2,3,4]`.

## Revision history

1. Implemented the fixed palette-column histogram with 8-connected flood fill. No earlier failed implementation was made.
