# Post-repair visible-only solve notes

Earlier exposure: **yes**. I reviewed the assigned generator before this solve, so
this is not blind. During the solve itself I did not reopen generator source,
Racket source, reference solutions, private labels, or prior solution explanations.

## Visible-example observations

1. Input and output dimensions and color counts are unchanged in all three examples.
2. Treating each row as adjacent two-cell chunks explains every movement. For a
   10-column row, chunks at columns `[0:2], [2:4], ..., [8:10]` appear in the
   reverse chunk order in the output.
3. The order *inside* each two-cell chunk is preserved. Example 0 begins with
   `[7, 9]`, which appears as `[7, 9]` at the far right rather than `[9, 7]`.
   This rejects ordinary horizontal reflection.
4. The same operation explains the centered chunk in example 2: the occupied
   chunks move from macro-columns 5, 4, 3 to macro-columns 1, 2, 3 while each
   `[7,4]/[4,7]` motif remains internally unchanged.
5. Empty chunks participate exactly like occupied chunks; there is no need to
   detect objects or infer a background color.

## Hypothesis tested

Partition every row into consecutive width-2 tiles, reverse the tile list, and
flatten it without reversing cells within a tile. This is equivalent to mapping
output chunk `j` to input chunk `n-1-j` for `n = width/2`.

## Alternatives rejected from visible evidence

- Whole-row reflection: would reverse each motif internally, contradicting
  examples 0 and 2.
- Moving only nonzero 2x2 objects: unnecessary and would be underspecified for
  rows containing partially empty motifs; chunk reversal handles those exactly.
- Reflecting the macro-grid vertically or rotating it: row indices never change.

The implementation validates a nonempty rectangular grid with even width and then
applies the row-wise chunk reversal directly.
