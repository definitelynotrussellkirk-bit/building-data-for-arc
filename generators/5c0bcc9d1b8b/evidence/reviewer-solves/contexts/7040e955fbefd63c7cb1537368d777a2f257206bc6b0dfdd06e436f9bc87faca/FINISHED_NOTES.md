# Post-repair solve notes

This is a visible-example solve after earlier generator/rule exposure; it is not blind.
I did not consult the generator, Racket source, private labels, or prior solution text during this solve episode.

## Observations from the three visible examples

- Every input/output is an odd square with background 7, divider color 0, and motif color 5.
- The input has two complete parallel black dividers and a perpendicular centered black line that can be interrupted by gray inside the channel.
- In all three examples the parallel dividers are horizontal, so the track direction is horizontal. The output moves them to the rows immediately above and below the center row and retains the perpendicular center column.
- The irregular gray motif is replaced by a centered, one-cell-wide line along the track.
- Gray-cell count is preserved exactly: visible examples have 11, 7, and 7 gray cells and output lines of those lengths.
- Grid size alone cannot determine line length: the two 11×11 examples produce lengths 11 and 7.

## Hypothesis

1. Count all gray cells.
2. Detect track direction from the two complete black parallel divider lines.
3. Rebuild those parallel dividers one cell on either side of the grid center.
4. Retain the centered perpendicular black crossbar.
5. Draw a centered gray line along the track whose length equals the original gray count, overriding the crossbar at the center.

The first query contains two complete black columns, so it exercises the vertical analogue. The second query is horizontal like the demonstrations.

## Rejected alternatives

- **Map grid size to line length:** contradicted by the two 11×11 demonstrations with different gray counts/output lengths.
- **Use motif bounding-box span:** the first 11×11 motif spans only five columns but yields an 11-cell line.
- **Keep original wall distance:** visible input walls are farther from center than output walls; all outputs place walls at center ±1.
- **Always draw horizontally:** the first query has two complete vertical walls and a horizontal crossbar, so orientation must rotate with the track.

## Implementation

`solution.py` uses only pixel evidence: it counts gray cells, finds complete black rows or columns to determine orientation, reconstructs the centered dividers, and draws the centered gray line. It deliberately rejects an ambiguous orientation rather than silently guessing.
