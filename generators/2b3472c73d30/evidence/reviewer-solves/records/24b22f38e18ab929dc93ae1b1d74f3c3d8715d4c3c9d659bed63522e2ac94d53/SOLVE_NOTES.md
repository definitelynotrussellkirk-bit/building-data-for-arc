# Blind solve work log

I inspected only `solve-blind/challenge.json`.

## Visible pattern

Each transformable row contains exactly two nonzero cells of the same color.
The output fills every zero between those two endpoints with that color,
leaving all other rows unchanged.

Visible negative evidence matters:

- Training example 1 row 0 contains colors 3, 9, 3 and remains unchanged.
- Training example 1 row 10 contains three markers of color 5 and remains unchanged.
- Rows with no eligible endpoint pair remain unchanged.

Therefore the rule is not "fill between every repeated color" when a row has
extra nonzero cells. My implementation requires exactly two nonzero cells and
requires their colors to match. It preserves dimensions and does not mutate the
input grid.

## Test-query predictions

- Query 1: fill the spans between the two 3s, the two 4s, and the two 6s.
- Query 2: fill the spans between the two 2s, the two 8s, and the two 4s.

## Revision 1

Implemented the exact-two-equal-markers rule directly. No intentional negative
or fabricated failed attempt was made.
