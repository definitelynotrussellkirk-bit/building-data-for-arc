# Solve work log

## Exposure statement

I began from the visible examples produced by `blind prepare`. I did not open the
blind task's generator, Racket rule, canonical record, reference solution, private
labels, notes, or audit evidence.

## Revision 1 — center the foreground bounding box

Across all four training pairs, every nonzero cell and color is preserved and the
whole pattern undergoes one translation. The output bounding box starts at

- row `(grid_height - foreground_bbox_height) // 2`, and
- column `(grid_width - foreground_bbox_width) // 2`.

This centers the minimal nonzero bounding box; when an odd leftover margin cannot
be split evenly, the extra blank row or column remains below or to the right. The
pattern's internal zeros, geometry, and colors remain unchanged. Examples 0–3
respectively shift by `(1, 1)`, `(0, -2)`, `(-2, -3)`, and `(1, 0)`, exactly as
this rule predicts.

I implemented that translation directly. As a defensive behavior not exercised by
the examples, an all-zero grid is returned unchanged. Remaining uncertainty is
limited to whether color 0 is always the background; that interpretation is
consistent with every visible example.
