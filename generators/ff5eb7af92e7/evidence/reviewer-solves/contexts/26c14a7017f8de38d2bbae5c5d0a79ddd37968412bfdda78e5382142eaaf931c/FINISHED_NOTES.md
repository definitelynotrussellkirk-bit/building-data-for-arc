# Exposed solve notes — ff5eb7af92e7

This is a human-readable work log based only on the prepared visible examples.
I had earlier rule exposure during the generator review, so this is not a blind
solve; I did not reopen the generator, Racket source, reference solutions, or
private labels during this solve phase.

## Observations

1. Every input and output has the same dimensions, and zeros stay zero.
2. Processing is independent by row. In each nonempty row, the output preserves
   every occurrence of one nonzero color and replaces all other colors by zero.
3. The retained color is the row's most frequent nonzero color, not a global
   color. Train 0 row 0 is especially diagnostic: color 4 occurs twice while
   colors 5 and 2 occur once, and only the two 4s survive. This is not an
   absolute-majority requirement because 4 occupies only 2 of 4 nonzero cells.
4. Empty rows remain empty. All visible active rows have a unique frequency
   winner, so no tie behavior is needed to explain the examples.

## Predicted queries

For query 0, row winners are `1, 6, 6, empty, 2`.
For query 1, row winners are `6, empty, 5, 5, 3, empty, 1`.

## Implementation

Count nonzero values in each row, select the largest count, and retain only that
color at its original coordinates. A first-occurrence tie break is included only
for deterministic behavior outside the visible set.
