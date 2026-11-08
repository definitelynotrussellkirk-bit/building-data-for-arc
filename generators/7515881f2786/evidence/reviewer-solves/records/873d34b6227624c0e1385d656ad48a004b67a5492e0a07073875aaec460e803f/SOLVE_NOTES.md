# Solve work log

## Exposure declaration

Before this solve I had reviewed the assigned generator and its rule as part of
the required repair work, so earlier rule exposure is **yes**. During this solve
I did not reopen the generator, Racket source, reference solutions, private query
labels, prior solve explanations, or parametric evidence. This is my own work log,
not a captured model trace.

## Revision 1 — connect original cyan anchors on shared rows and columns

The visible outputs preserve the input shape and colors. Whenever two or more
original cyan (`8`) cells share a row, the zeros between consecutive anchors are
recolored cyan. The same operation applies to columns. Isolated anchors remain
unchanged.

The original-anchor qualification matters. In training example 2, filling the
three-anchor row creates a cyan cell in column 5 above another original anchor;
the output does **not** fill that new vertical gap. Therefore row/column anchor
locations must be read from the untouched input, while painting occurs in a copy.

For a line with three anchors, filling each adjacent pair is equivalent to
filling from the first through the last, but the adjacent-pair formulation keeps
the blocking semantics explicit. I implemented horizontal and vertical passes
that both inspect only `grid` and write only to `result`.

Predictions include: query 0 fills row 0 from columns 0 through 7 and column 2
from rows 0 through 5; query 1 fills row 0 from columns 1 through 13 and column 1
from rows 0 through 9. Other anchors remain isolated.
