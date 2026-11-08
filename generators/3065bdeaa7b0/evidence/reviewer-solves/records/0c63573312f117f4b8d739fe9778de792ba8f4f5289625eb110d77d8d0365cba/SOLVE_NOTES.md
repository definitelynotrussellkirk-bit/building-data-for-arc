# Fresh solve work log

This is a human-visible-example work log, not a hidden model trace. I had already
seen the task rule while repairing the generator, so this solve is **not blind**;
I deliberately restricted the solve phase itself to `solve/challenge.json` and did
not reopen the generator, Racket source, reference solutions, or private labels.

## Hypothesis 1

Every nonzero color that appears exactly twice defines two endpoints. Order those
endpoints lexicographically by `(row, column)`. From the earlier endpoint, paint a
horizontal segment to the later endpoint's column, then paint vertically to the
later endpoint. Process color-pair records by the first endpoint, so a later pair
wins at crossings.

Visible-example evidence:

- Training example 1 has two exact pairs and shows horizontal-then-vertical Ls.
- Training example 2 has color 4 three times; those three cells are not connected,
  while colors 8, 3, and 7 (each appearing twice) are connected.
- Several pairs begin at a top-right endpoint and run left, ruling out a fixed
  left-to-right endpoint rule.
- Crossings in training example 2 show later top-to-bottom pair processing can
  overwrite an earlier path.

## Implementation

`solution.py` counts positions, keeps only exact pairs, lexicographically orders
endpoints and pair records, copies the input, then paints the two inclusive legs.
No query-specific constants are used.
