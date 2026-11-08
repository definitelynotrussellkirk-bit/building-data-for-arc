# Solve work log

Earlier rule exposure: no. I had not opened the task generator, Racket rule,
reference solutions, labels, notes, or audit material. I used only the visible
examples in `challenge.json`.

## Observation and hypothesis

Every training input is a small output grid expanded by independently repeating
whole rows and whole columns. Within a row band, every input row is identical;
within a column band, every input column is identical. The run lengths vary by
band and example, so fixed-size pooling is not plausible.

For example, the first training input has row-run lengths 3, 2, 2, 6, 4 and
column-run lengths 2, 3, 3, 2. Keeping one representative from each consecutive
run gives exactly the shown 5x4 output. The second and third examples give the
same rule with different run lengths and output shapes.

## Program

The solution first removes consecutive duplicate rows. It then compares adjacent
columns across those retained rows and keeps one column from each consecutive
identical run. Empty input is handled conservatively as an empty output.

## Alternatives considered

- Sampling at a fixed stride was rejected because the band widths are unequal.
- Taking globally unique rows or columns was rejected because a pattern could
  legitimately recur after an intervening band; only adjacent repetitions encode
  expansion.
- Connected-component or color-frequency rules were unnecessary and would not
  explain the rectangular Cartesian band structure.

## Expected test outputs

The first query compresses to `[[0, 1], [9, 0], [3, 9]]`.
The second query compresses to `[[8, 3, 5], [6, 2, 5]]`.
