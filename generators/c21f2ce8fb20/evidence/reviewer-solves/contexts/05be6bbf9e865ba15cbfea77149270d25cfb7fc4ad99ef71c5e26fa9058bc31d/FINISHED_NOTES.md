# Blind solve notes — c21f2ce8fb20

## Observations

- The gray `5` cells are separators/background. Each connected region of non-gray
  cells is a rectangular panel containing black `0` cells and a few red `2` cells.
- The output discards all gray separators and unselected panels, making the canvas
  black `0` except for one panel-sized azure `8` rectangle.
- Across the four demonstrations, the selected panel is exactly the one with the
  largest number of red cells: counts are respectively `2`, `3`, `4`, and `3`.
  Competing panels in those examples have fewer red cells.

## Hypothesis

Find every 4-connected component of cells that are not gray `5`, count its red
`2` cells, select the component with the greatest red count, and fill its bounding
rectangle with azure `8` on an otherwise black output of the same dimensions.

## Predicted queries

- Query 0: select rows 2–3, columns 7–9 (two red cells); the other panels each
  contain one red cell.
- Query 1: select rows 1–3, columns 1–3 (three red cells); the alternatives contain
  one, two, and one red cells.

## Implementation notes

The solver uses 4-neighbor flood fill so it does not depend on a fixed panel size,
position, count, or layout. A visible-example regression test was written first;
it failed against the template and then passed after implementing the rule.
