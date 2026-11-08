# Blind solve work log — d0d18b0499a5

## Observation
Every demonstrated output is blank except for horizontal color-8 spans. A span
appears exactly on a row that contains two non-background input cells, and its
endpoints are those two occupied columns. Rows with one, three, or four occupied
cells contribute nothing. The original marker colors do not affect the output.

## Hypothesis
For each row independently: if it has exactly two nonzero cells, paint the
inclusive interval between them with 8; otherwise leave the output row all zero.
The output preserves the input dimensions and discards every original marker.

## Checks against visible examples
- Example 1: rows with marker counts 2 at columns 1–4 and 5–10 become the two
  shown spans; the three-marker and one-marker rows disappear.
- Example 2: only the 6–12 and 0–3 pairs survive, despite mixed endpoint colors.
- Example 3: only rows 7 (8–12) and 10 (13–15) contain exactly two markers.

## Implementation
Implemented the rule directly with a per-row list of nonzero column indices.
No reference rule, generator source, private labels, or prior solution was read.
