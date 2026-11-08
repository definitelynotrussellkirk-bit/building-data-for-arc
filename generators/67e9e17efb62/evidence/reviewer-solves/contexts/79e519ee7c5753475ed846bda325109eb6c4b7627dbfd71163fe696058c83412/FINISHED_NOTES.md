# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solutions, private
labels, audit records, or earlier solution explanations. I used only the visible
examples printed by `python3 review.py blind prepare` and a local calculation of
flattened output positions.

## Revision 1 — diagonal run serialization

### Observation

The input has one nonzero horizontal bar. Let its color be `c` and its length be
`n`. Every output contains exactly `n²` cells of color `c`:

- the two `n = 6` examples contain 36 colored cells;
- the `n = 5` example contains 25 colored cells.

Flattening either `n = 6` output row-major gives exactly the same sequence even
though the input bar is on a different side and the output widths are 11 and 16.
The colored run lengths between single zero separators are
`1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1`. For `n = 5`, they are
`1, 2, 3, 4, 5, 4, 3, 2, 1`. Thus the apparent two-dimensional pattern is a
one-dimensional serialization of the diagonals of an `n × n` solid square,
wrapped at the original input width and zero-padded at the end.

### Program

1. Count all nonzero input cells to obtain `n` and take their value as `c`.
2. Build runs of `c` with lengths `1..n..1`, inserting one zero between adjacent
   runs.
3. Pad the final partial row with zeros and reshape to the input width.

### Alternatives considered

I considered whether the bar's left/right placement controlled direction, but the
two `n = 6` training outputs have the same flattened stream, so placement is not
used. I also considered a direct geometric square/diamond output, but the varying
output height and invariant row-major stream support serialization and wrapping.

### Remaining uncertainty

The visible domain contains one nonzero color and one solid bar, so the program
uses the total nonzero count. If unseen inputs contained several objects or colors,
that would be outside the demonstrated domain.
