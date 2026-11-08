# Fresh solve notes

This is a human work log, not a captured model trace. The solve episode followed
generator review, so I had earlier rule exposure and do **not** claim blindness.
During this phase I read only `solve/challenge.json`; I did not reopen the
generator, Racket source, canonical ledger, reference solution, or private labels.

## Visible-example observations

- Each input contains three nonzero colors and each output is a tight all-8
  rectangle. Output dimensions match one colored candidate's row/column extent.
- Choosing by color, count, largest bounding box, or position does not fit all
  five demos. For example, the first demo's selected 2 has only four corner
  cells, while later examples contain larger or denser decoys.
- A rule that does fit every demo is: treat each color separately, fill gaps
  between same-color cells on each occupied row, then fill gaps between the
  resulting cells in each occupied column. Exactly one color becomes its full
  bounding rectangle. Emit that rectangle as cyan (8).

## Implementation decision

`solution.py` mirrors that structural operation directly. It computes row
closure, then column closure, compares the result with each color's full bounding
box, requires a unique winner, and returns an all-8 grid of the winner's height
and width. It does not mutate the input and has no task-specific color choice.

## Stopping reason

The first implementation matches all visible training examples and expresses the
smallest structural rule that survives their count, color, size, and position
contrasts. No revision was needed after visible-example checking.
