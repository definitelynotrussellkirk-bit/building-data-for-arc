# Blind solve notes — dcc5f8961845

This is a human work log made only from `challenge.json` and local Python reasoning.
No generator, Racket rule, canonical source, private labels, prior solution, or audit
record was consulted.

## Hypothesis 1

The lower nonzero pattern is cropped to its bounding rectangle.  A compact header
at the start of row 0 controls clockwise quarter turns.  The three demonstrations
show header-first values `5 -> 2 turns`, `3 -> 1 turn`, and `0 -> 0 turns`; the
smallest rule fitting them is `turns = floor(first_value / 2) mod 4`.  The second
header cell is not needed by this hypothesis.  This may be an underdetermined code,
so the masked tests remain uncertain, especially for first values 0 and 4.

Implementation crops all nonzero cells below the header row, preserving zeros
inside the bounding box, then applies the inferred clockwise turns.
