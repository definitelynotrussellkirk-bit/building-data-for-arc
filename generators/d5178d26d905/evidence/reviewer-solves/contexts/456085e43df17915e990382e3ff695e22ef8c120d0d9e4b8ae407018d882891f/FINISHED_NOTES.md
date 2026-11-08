# Visible-only solve notes

## Observations

- Every input has exactly one column made entirely of gray `5`; it separates two panels.
- Rows that are all gray inside a panel are padding and disappear from the output logic.
- Exactly one active panel uses only `0` and yellow `4`. Its dimensions match the output, so I call it the **reference**.
- The other panel is a colored **template**. Its most frequent active row is a sparse vertical-line row: every nonzero position supplies one line color.
- In the reference, the positive-yellow row with the fewest yellows supplies the output line positions. Zero rows and repeated copies of that row behave normally.
- Other positive-yellow rows are special rows. They map, top-to-bottom, to the template's non-mode rows, also top-to-bottom.

## Special-row hypothesis

For a special template row, the first position outside the ordinary line columns is its fill color. A special output row is filled with that color. At each reference line position, retain the ordinary line color only when the corresponding template special cell still equals that ordinary line color; otherwise use the fill.

This explains, for example, why a template special row that is one solid color can produce a solid output row, while a row retaining only some ordinary line colors preserves only those lines.

## Alternatives rejected from the visible examples

- **Match panels by raw row index:** rejected because gray padding moves the template vertically while the special rows still map by order.
- **Use every yellow reference row as special:** rejected because the sparsest positive-yellow pattern occurs as the ordinary line-position key.
- **Copy special template rows directly:** rejected because template and reference widths differ; the template encodes colors/retention while the reference encodes positions.
- **Match special rows by color or yellow count:** unnecessary and contradicted by the consistent top-to-bottom pairing across examples.

## Implementation

1. Locate the all-`5` divider and crop all-gray padding rows from each side.
2. Identify the 0/4 reference panel.
3. Take the modal template row, its nonzero columns, and their colors.
4. Take the minimum-positive-yellow reference row and its yellow columns.
5. Pair non-normal rows by order and repaint the reference as described above.
