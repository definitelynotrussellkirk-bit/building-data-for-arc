# Solve notes

This is a human work log written from the prepared visible examples. I had already
seen the task rule while repairing its generator, so this is an exposed rather
than blind solve; I did not reopen the generator, Racket authority, reference
solutions, or hidden labels during this solve episode.

## Hypothesis

There is one connected nonzero multi-cell object. It is a stamp/template and
contains at least one maroon 9. Every isolated 9 is a destination marker. Place a
translated copy of the entire template at each marker by aligning the template's
anchor 9 to the marker, discard cells outside the canvas, count copy coverage,
and render counts as 1 -> red 2, 2 -> green 3, and 3+ -> yellow 4.

The examples with multiple 9s inside the template disambiguate which 9 is the
anchor. Reconstructing the component in row-major discovery order with BFS
neighbors up, down, left, right, the selected anchor is the last 9 visited. This
choice reproduces the visible double- and triple-overlap locations.

## Implementation

`solution.py` independently finds nonzero 4-connected components, identifies the
multi-cell template and singleton markers, derives the anchor from BFS order,
accumulates translated coverage in a fresh grid, and maps counts to output colors.
The original template itself is not copied unless an isolated marker calls for a
copy there.
