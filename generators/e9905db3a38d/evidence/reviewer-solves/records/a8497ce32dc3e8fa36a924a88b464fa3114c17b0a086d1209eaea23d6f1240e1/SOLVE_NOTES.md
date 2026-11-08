# Solve notes — e9905db3a38d

## Policy and prior exposure

I read only `solve/challenge.json` during this solve episode. I did not open the
Racket rule, generator implementation, reference solution, private labels, or
previous solution explanations during the solve. I had already seen and analyzed
the task rule earlier while completing the assigned generator review, so this is
**not** a blind solve; I will finish with `--earlier-exposure yes` and
`--reference-consulted no`.

## Visible-example observations

1. Each input has two colored shapes in the area above the final two rows: one
   color-1 shape and one color-2 shape. Their bounding boxes are equal squares.
2. The final two rows contain a narrow contiguous block of values 1–4, with zeros
   elsewhere. The output has two tile rows and one tile column per active code
   column.
3. Output tiles preserve the template colors and shapes. Adjacent tiles have one
   all-zero row or column between them.
4. Comparing codes against visible outputs suggests:
   - 1 = color-1 template unchanged
   - 2 = color-2 template unchanged
   - 3 = color-1 template rotated clockwise
   - 4 = color-2 template rotated clockwise

## Hypothesis

Crop the color-1 and color-2 template bounding boxes from all rows except the last
two. Find the minimum and maximum non-zero code columns. Allocate a 2-by-N mosaic
of template-sized slots separated by one-cell gutters. Decode each code with the
mapping above and paste non-zero template cells into its slot.

## Probe plan

Implement the direct decoder, then check all three visible training examples. If
any fail, separately inspect (a) rotation direction, (b) whether the code span
includes zero-only interior columns, and (c) whether template crops preserve bbox
zeros. The initial implementation preserves bbox zeros, uses clockwise rotation,
and includes every column between the first and last non-zero code column.
