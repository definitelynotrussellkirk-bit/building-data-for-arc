# Visible-only solve notes

This is a human work log based only on `solve/challenge.json`. I had earlier
exposure to the task rule while repairing the assigned generator, so this is an
exposed solve, not a blind inference record. I did not reopen the generator,
Racket rule, reference solution, or private labels during this solve.

## Hypothesis from the three visible demonstrations

The output starts as an all-zero grid. Scan each input column into maximal
same-colour nonzero vertical runs. A run produces output only when:

1. its length is exactly three; and
2. its column is not the left or right edge.

For each qualifying run, paint a horizontal run of the same colour and length
three on the input run's middle row, centered on its original column. All input
pixels from nonqualifying runs disappear; they are not copied through.

Visible counterevidence fixes the boundaries rather than merely suggesting a
rotation:

- train 1 has a length-4 colour-1 run, a length-2 colour-3 run, and an edge
  colour-9 trio; all disappear;
- train 2 again includes edge, length-2, and length-4 negatives, while only the
  two interior trios appear horizontally;
- train 3 has the same three negative categories and two positive trios.

## Implementation choice

I implemented a columnwise maximal-run scanner. It uses a fresh zero output,
requires exact length 3, rejects side-edge columns, and paints the three centered
horizontal cells. This directly handles multiple runs of the same colour in one
column when separated by zeroes and avoids component-order assumptions.
