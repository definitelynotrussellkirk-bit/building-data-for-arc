# Blind solve notes — 983d0ea3bd17

## Attempt 1 — cross rays with opaque non-red blockers

Observed that every red (`2`) cell paints orange (`7`) along its row and column while preserving the source. In training examples 1 and 3, unobstructed rays continue to the grid boundary. In training example 2, the `3` and `8` cells two columns to the right of red sources remain unchanged and no orange appears beyond them, so non-red foreground cells appear to be opaque blockers. Red cells are treated as transparent/source cells; zeros traversed by at least one ray become `7`.

Probe encoded directly: scan from every red source in four cardinal directions against the untouched input, stop at the first nonzero cell other than red, preserve all nonzero cells, and paint traversed zeros orange. This predicts full crosses in test 1; in test 2 the colored cells at column 6 block the leftward rays from the red cells at column 8, while the red at row 3/column 7 remains unobstructed.
