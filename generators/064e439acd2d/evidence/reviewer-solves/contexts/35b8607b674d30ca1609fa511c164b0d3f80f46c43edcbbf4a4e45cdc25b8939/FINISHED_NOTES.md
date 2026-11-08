# Solve notes

The visible examples contain one solid cyan line or rectangle and colored cells outside it. The output preserves every source cell. A source whose row crosses the cyan bounding box is copied to the nearest left/right edge cell; a source whose column crosses it is copied to the nearest top/bottom edge cell. A source diagonal to the box is ignored. This explains the repeated 5 in example 0, the right-side 2 in example 1, the touching and below sources in example 2, and the top/bottom sources in example 3.

Implementation: find the bounding box of all 8 cells, copy the grid, then project each nonzero non-8 source only when its row or column lies within the box. Row alignment is checked first, although the supplied exterior sources do not require a collision policy. I did not inspect generator or reference source after solve preparation. I had earlier rule exposure during the assigned generator review, so the final exposure declaration is `yes`.
