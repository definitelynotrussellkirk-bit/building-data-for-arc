# Blind solve notes — b9d1d323c3ed

## Observation

Each visible input contains one nonzero pattern embedded in a zero background.
The output dimensions equal the tight nonzero bounding-box height and twice its
width. In every training pair, the output is the tight crop repeated twice
side-by-side without reflection or recoloring.

- Train 0: 3×3 crop becomes 3×6 by horizontal duplication.
- Train 1: 12×4 crop becomes 12×8 by horizontal duplication.
- Train 2: 3×3 crop becomes 3×6 by horizontal duplication; internal zero rows
  and cells are retained, so this is bounding-box cropping rather than extracting
  only colored cells.

## Hypothesis

Find the tight bounding rectangle of all nonzero cells, preserve every cell in
that rectangle, and concatenate each cropped row with itself.

## Predicted queries

- Query 0 crop: `[[3,3],[0,3]]`; predicted output is
  `[[3,3,3,3],[0,3,0,3]]`.
- Query 1 crop: `[[9,0,9],[0,9,0],[9,0,9]]`; predicted output repeats each row,
  producing a 3×6 grid.

No generator, rule, private label, prior solution, or audit record was consulted.
