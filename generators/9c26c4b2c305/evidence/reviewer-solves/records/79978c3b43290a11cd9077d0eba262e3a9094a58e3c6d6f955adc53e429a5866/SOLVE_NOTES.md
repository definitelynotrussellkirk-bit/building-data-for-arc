# Visible-example solve log

## Revision 1

The input is two equal-height panels separated by one solid row. Across all four
visible demonstrations, the output has the panel height and width, clears the
separator, and uses only 0 and 3. At each aligned coordinate the output is 3
whenever the top cell or the bottom cell is nonzero, including the cases where
both are occupied; it is 0 only when both are 0. The particular panel colors and
separator color vary, so they are role markers rather than literals.

Implementation: locate the unique nonzero full-width constant separator, verify
two equal-height panels, and apply coordinatewise occupancy OR, coloring true
cells 3. This was derived only from `solve/challenge.json`. I had earlier rule
exposure from the generator-review phase, so this is an exposed post-repair
solve rather than a blind solve; I did not consult the Racket source or a
reference solution during this solve episode.

## Revision 2

Revision 1 incorrectly selected the *first* full nonzero row as the separator.
One visible demonstration contains a completely occupied panel row before the
actual divider, so execution chose that row and the equal-panel check failed.
The examples instead establish a centered divider: every input has an odd row
count, equal panels, and a solid nonzero middle row. I changed separator
selection to the middle row and retained the same coordinatewise occupancy-OR
hypothesis.
