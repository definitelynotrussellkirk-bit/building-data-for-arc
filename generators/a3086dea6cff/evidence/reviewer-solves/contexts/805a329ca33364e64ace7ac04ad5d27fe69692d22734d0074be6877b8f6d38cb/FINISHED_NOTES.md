# Blind solve notes — a3086dea6cff

This is a human reasoning work log based only on `challenge.json`.

## Hypothesis 1

For each nonzero color, act only when it occurs **exactly twice**. If the two
cells share a row, fill the inclusive horizontal segment; if they share a
column, fill the inclusive vertical segment. Ignore colors with more than two
occurrences and exactly-two colors whose cells are diagonal.

Evidence from the visible examples:

- Example 1 connects the two 3s vertically, the two 6s horizontally, and the
  two 4s horizontally.
- Example 2 leaves color 2 unchanged because it has three markers, while the
  exact pairs 6, 3, and 7 are connected.
- Example 3 leaves the diagonal pair of 9s unchanged while connecting the 8,
  2, and 5 pairs.

At the two visible crossings (3/6 in example 1 and 2/5 in example 3), the
horizontal segment occupies the crossing cell. I therefore paint vertical
segments first and horizontal segments second. This precedence is observable,
not inferred from color magnitude.

## Probe / implementation

Implemented the rule directly with a color-to-coordinate census. No hidden
reference, generator, prior solution, or private label was consulted.
