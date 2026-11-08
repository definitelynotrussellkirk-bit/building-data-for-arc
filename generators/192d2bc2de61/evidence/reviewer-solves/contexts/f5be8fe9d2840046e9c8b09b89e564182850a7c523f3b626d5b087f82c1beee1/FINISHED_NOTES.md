# Solve work log

Earlier exposure before this solve: none. I did not inspect the task's generator,
Racket rule, reference solution, private query labels, prior notes, or the assigned
repair generator before completing this visible-only attempt.

## Hypothesis

The input contains a sparse color-order key above a long horizontal blank gap and
a bank of colored glyphs below it. The first occupied row of the upper key lists
all glyph colors in the desired left-to-right order. For each listed color, crop
the corresponding lower glyph to its bounding box, preserve zeros inside that
box, and concatenate the cropped glyphs with one blank column. The glyphs are
top-aligned and the output height is the tallest glyph.

Evidence from the visible examples:

- Example 0 key order is 7, 5, 8; the output contains the lower 7, 5, and 8
  glyphs in exactly that order.
- Example 1 key order is 7, 8, 3; the output changes to that order without
  rotating or recoloring the lower shapes.
- Example 2 key order is 6, 1, 8; bounding-box widths explain the 10-column
  output as glyph widths plus two single-column separators.

## Implementation choices and uncertainty

I split upper and lower regions at the largest gap between occupied rows rather
than using a fixed row number. I read the order from the first occupied upper
row, deduplicating colors, and find each glyph only below the split so the key's
own colored cells cannot affect its crop. Shorter glyphs are padded with zeros at
the bottom by top-aligning them in the tallest output canvas.

The visible data consistently places every order color once in the first occupied
key row and one glyph of each color below. The solution intentionally reports an
error if either contract is absent rather than silently guessing.
