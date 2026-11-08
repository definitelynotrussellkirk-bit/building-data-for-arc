# Blind solve work log

## Observation
Each output preserves the input and sometimes fills a straight segment between two cells of the same nonzero color.

- Example 0: the two 6s share a column, so the cells between them become 6; the two 4s share a row, so the horizontal gap becomes 4.
- Example 1: each of 3, 7, and 8 occurs exactly twice and its pair is row- or column-aligned; every corresponding gap is filled.
- Example 2: 4 and 9 are aligned pairs and are connected. The two 8s are diagonal, so they are unchanged.
- Example 3: the aligned pair of 4s is connected. Color 6 has three cells, not exactly one pair, so it is unchanged; the singleton 9 is unchanged.

## Hypothesis
For every nonzero color that occurs exactly twice, connect its two cells inclusively when they share a row or a column. Leave diagonal pairs, singleton colors, and colors with any other multiplicity unchanged.

## Queries predicted
- Query 0: connect 2 horizontally on row 3, columns 4..6; connect 8 vertically on column 2, rows 4..7.
- Query 1: connect 7 horizontally on row 1, columns 0..4; connect 3 horizontally on row 4, columns 3..5; connect 4 vertically on column 2, rows 4..7.

No reference source, generator source, private label, prior solution, or task note was consulted.
