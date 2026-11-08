# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference outputs, private query labels, audit evidence, or any prior solution explanation. I only used the visible grids printed by `blind prepare` and the generated visible-only README.

## Revision 1 — quadrant markers replace the 2×2 block

Across all three demonstrations, color 8 forms a 2×2 block. Four other colors occur once each, with one singleton in each diagonal quadrant around that block. The output clears everything and writes those four singleton colors into the corresponding cells of the former 2×2 block:

- marker above and left → top-left cell;
- marker above and right → top-right cell;
- marker below and left → bottom-left cell;
- marker below and right → bottom-right cell.

Example 0 maps 4, 7, 9, 3 into `[[4, 7], [9, 3]]`; example 1 maps 9, 4, 2, 6; example 2 maps 1, 7, 5, 4. Their exact distances from the block vary, so distance is irrelevant and only the quadrant matters.

I implemented the literal rule with validation for one 2×2 color-8 block and one marker per quadrant. Remaining uncertainty: the visible examples do not show a marker sharing a row or column with the block, but every supplied instance places markers strictly outside it, so the strict quadrant interpretation is supported.
