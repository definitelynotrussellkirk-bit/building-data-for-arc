# Blind solve notes — task 323fded12174

## Visible-only observations

- Every example preserves each row exactly and only changes row order.
- Color 0 is empty/background in all visible examples.
- One non-zero color is far more frequent than the others and forms the plain
  geometric rows: 9 in examples 0 and 2, and 5 in example 1.
- Exactly two rows contain additional non-zero colors. These appear first in
  the output, ordered by *increasing* count of the frequent structural color.
- Rows containing only background plus the structural color follow, ordered by
  *decreasing* count of the structural color.

Concrete checks:

- Example 0 key rows contain 2 and 3 structural 9s, producing input rows 6, 0.
  Plain-row 9-counts are 6, 5, 3, 2, 1, producing rows 3, 4, 2, 1, 5.
- Example 1 key-row 5-counts are 3 and 6, producing rows 3, 0. Plain-row
  5-counts are 6, 5, 4, 1, producing rows 2, 1, 5, 4.
- Example 2 repeats example 0's structure with different accent colors.

## Hypothesis implemented

1. Choose the most frequent non-zero color as the structural/fill color.
2. A key row contains at least one color other than 0 or the fill color.
3. Stable-sort key rows by fill count ascending.
4. Stable-sort all other rows by fill count descending.
5. Concatenate the two groups without changing any row contents.

For equal counts, retaining input order is the least-assumptive tie behavior.
The two visible queries both have a clear dominant non-zero fill color and two
accent-bearing key rows, so no additional fallback is needed beyond returning an
all-zero grid unchanged.
