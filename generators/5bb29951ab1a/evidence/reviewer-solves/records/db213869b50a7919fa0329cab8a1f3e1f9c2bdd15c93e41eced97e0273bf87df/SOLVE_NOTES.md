# Solve work log

I had not opened any generator, canonical rule, reference solution, audit evidence,
or private query label before this solve. I used only the visible challenge produced
by `python3 review.py blind prepare`.

## Observation and hypothesis

Every input contains background color 0, one dominant nonzero fill color, and one
sparse nonzero corruption color. The output removes every corruption-colored cell.
A corrupted cell is restored to the dominant fill when it lies inside a filled
rectangle or in a one-cell separator position directly joining fill on opposite
sides; otherwise it is restored to background.

Across the four visible examples, that distinction has a simple local witness:
all cells restored to fill have at least two orthogonally adjacent fill-colored
neighbors, while border/background corruptions have at most one. Examples include
the vertical bridge at train 0 `(6,3)`, horizontal bridge at train 1 `(7,5)`,
vertical bridge at train 2 `(6,13)`, and horizontal bridge at train 3 `(10,7)`.

## Implementation choice

1. Count nonzero colors and treat the most frequent as the fill color.
2. Preserve existing background and fill cells.
3. For each other-colored cell, count its four orthogonal neighbors equal to the
   fill color. Restore it to fill for count >= 2, else to background.

I considered reconstructing whole rectangular masks from row/column spans, but the
local criterion is the smallest rule that explains every visible change and avoids
inventing filled cells away from an observed corruption. Remaining uncertainty:
a future instance with a large multi-cell corruption hole could require iterative
or rectangle-level reconstruction, but no visible example supports that extension.
