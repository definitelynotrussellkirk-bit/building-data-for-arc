# Visible-only solve notes

Earlier rule exposure is **yes** because I had already reviewed this task's generator and selected Racket authority. For this final-source solve I read only `solve/challenge.json`; I did not reopen the generator, Racket source, reference solutions, private labels, or the prior solve record.

## Hypothesis from the visible examples

Each input has two colors. One color forms complete horizontal and vertical divider runs. The other fills every rectangular region between those runs. The output is a fresh monochrome grid: its height is the number of contiguous non-divider row bands, its width is the number of contiguous non-divider column bands, and its color is the region color.

The first and third visible examples include two-cell-thick divider runs, while other examples have unit dividers and edge dividers. Therefore the robust operation is to count *contiguous runs of non-divider coordinates*, not individual divider rows/columns plus one.

## Implementation

Find the unique color with at least one complete row and complete column. Collect all complete rows and columns of that color, count contiguous runs in their complements, and fill the resulting rectangle with the other color.
