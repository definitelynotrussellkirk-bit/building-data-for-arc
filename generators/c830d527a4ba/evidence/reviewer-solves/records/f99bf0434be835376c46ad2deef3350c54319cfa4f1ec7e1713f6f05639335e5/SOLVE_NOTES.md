# Solve work log

## Hypothesis 1

The color-1 object is a source template.  The separate rectangular bbox made
from colors 2–5 is a code grid (zeros inside that bbox are meaningful blank
codes).  Each code expands to a recolored template transform:

- 2: identity
- 3: 90 degrees clockwise
- 4: 180 degrees
- 5: horizontal reflection
- 0: a blank tile with the untransformed template dimensions

Within each code row, transformed tiles are floor-centered vertically and
separated by one blank column.  The resulting tile rows are floor-centered
horizontally in the widest row and separated by one blank row.  This explains
all three visible outputs, including the varying widths/heights produced by the
90-degree transform and the blank middle code in training example 3.

I implemented this directly from the visible examples.  I had seen the task's
rule earlier while repairing its generator, so this is an exposed rather than
blind solve; I did not consult a reference implementation during this episode.
