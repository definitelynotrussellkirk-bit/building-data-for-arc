# Blind solve notes — 9ff30d18e156

This is a human visible-example work log. I did not consult generator code, the
Racket authority, reference solutions, private labels, prior explanations, or
audit records.

## Hypothesis

Each row is independent. For every non-background color that occurs at least
twice in a row, fill the complete horizontal interval from its leftmost to its
rightmost occurrence with that color. A color occurring once is left unchanged.
The visible examples have disjoint intervals for different colors in the same
row, so no overlap tie-break is needed.

## Evidence from visible examples

- Training 1: the two 9s, two 7s, and two 5s each become solid horizontal bars.
- Training 2: already-partial bars such as 9 at columns 0,2,3 and 8 at 7,8,10
  are completed only inside their extreme endpoints; singleton 4/5/1/7 cells stay.
- Training 3: multiple occurrences of 7 or 5 define the same extreme-endpoint
  fill even when more than two anchor cells are present.

## Probe and implementation

I grouped nonzero cells by row and color, then filled `min(column)..max(column)`
when the group size was at least two. I preserved all other cells. This predicts
separate bars in test rows containing multiple repeated colors and leaves rows
with only singletons unchanged.
