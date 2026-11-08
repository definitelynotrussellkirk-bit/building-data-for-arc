# Post-repair visible-only solve notes

## Observations

- The top-left value is a command: train 0 and train 2 use `1`; train 1 uses `2`.
- Every non-command colour occurring exactly twice becomes an L connecting its two markers.
- Markers are ordered row-major. With command `1`, the horizontal leg lies on the first marker's row and the vertical leg lies on the second marker's column. With command `2`, the vertical leg lies on the first marker's column and the horizontal leg lies on the second marker's row.
- A colour occurring three times is not routed: train 2 leaves the three `4` cells unchanged. The extra command-colour cells are also excluded.
- At crossings, process colours in first-appearance order so later colours overwrite earlier routed cells, matching the visible examples.

## Implementation

Scan the input once to retain row-major colour order and marker positions. Copy the grid. Skip background, the command colour, and every colour whose count is not exactly two. Paint the selected L orientation inclusively for each remaining colour.

## Exposure disclosure

This solve is not blind: I had earlier rule exposure while repairing the generator. During this solve phase I used the newly displayed visible examples and did not reopen the generator, Racket rule, reference outputs, or private labels.
