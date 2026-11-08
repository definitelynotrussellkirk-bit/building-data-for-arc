# Visible-only solve notes — 563e1df172df

This is a human work log based only on `solve/challenge.json`. I had earlier exposure to the task's implementation during the repair, but I did not consult the generator, Racket rule, reference solutions, or private labels during this solve episode.

## Observations

- Every input contains one red cell (`2`) and one green cell (`3`) on different rows and columns.
- The output preserves both endpoints and adds color `8` on an orthogonal path.
- The elbow is always at **red's row and green's column**: travel horizontally from red until reaching green's column, then vertically in that column toward green.
- The four demonstrations cover red left/right and above/below green. The first demonstration has adjacent rows, so the vertical arm has no interior cell; this confirms that endpoints are preserved rather than overwritten.

## Hypothesis

Copy the input. Fill the cells strictly between red's column and green's column on red's row with `8`. Then fill cells strictly between red's row and green's row in green's column with `8`. Leave red and green unchanged.

## Alternatives rejected from visible evidence

- **Vertical-first elbow (red column, green row):** contradicted by demonstrations 2–4.
- **Only a straight horizontal arm:** contradicted by demonstrations 2–4, which require a visible vertical arm.
- **Only a straight vertical arm:** contradicted by every demonstration with a multi-cell horizontal gap.
- **Shortest-path choice based on endpoint quadrant:** all quadrants use the same red-row/green-column elbow.

## Implementation

`solution.py` locates the unique `2` and `3`, copies the grid, paints only the interior cells of the horizontal and vertical arms, and returns the copy. I stopped after the first evidence-backed implementation because one rule explains all four visible pairs without exceptions.

## Revision 1 result and correction

The first implementation passed neither visible pair because it painted cells *strictly* between the endpoint columns and therefore left the elbow `(red row, green column)` as background. Re-reading the visible outputs showed that the elbow is part of the path and must be `8`. The vertical arm still excludes green, but the horizontal loop now includes green's column. No other rule assumption changed.
