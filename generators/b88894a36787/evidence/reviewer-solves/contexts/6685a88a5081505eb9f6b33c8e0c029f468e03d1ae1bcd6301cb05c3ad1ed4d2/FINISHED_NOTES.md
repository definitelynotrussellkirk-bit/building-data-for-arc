# Solve notes

## Visible evidence

Each 12×12 training input has a contiguous run of three colored cells in row 0. A same-colored singleton may occur on the left or right boundary below it. The output turns each such pair into an L: vertical from the header cell to the singleton's row, then horizontal to the boundary singleton.

Training examples 0 and 2 also expose the missing-pair case. Color 5 in example 0 and color 4 in example 2 have no matching boundary singleton; each continues vertically through the final row with no horizontal segment. That rules out “only connect colors that occur twice.”

## Hypothesis used for revision 1

1. Read nonzero row-0 cells left to right as header entries.
2. For each header color, find its first matching nonzero body cell in row-major order.
3. With a match, paint the vertical segment down to its row and the horizontal segment to its column.
4. Without a match, paint the header column through the bottom row.
5. If paths ever overlap, use header order as deterministic priority. The visible examples do not require resolving an overlap, so this detail is conservative rather than demonstrated.

The two queries exercise all-left complete connectors and an interior missing color, respectively. No alternative visible hypothesis explains the missing-color bottom extension as directly.
