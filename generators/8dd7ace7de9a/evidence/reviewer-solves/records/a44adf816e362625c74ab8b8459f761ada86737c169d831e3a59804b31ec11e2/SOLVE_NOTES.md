# Solve work log

Earlier exposure: none to task `8dd7ace7de9a`; I did not open its generator, rule,
private labels, prior solutions, notes, or audits. I used only `challenge.json`.

## Revision 1 — periodic lattice restoration

Across all three visible pairs, one dominant color is the clean background, one
non-background color forms intersections of periodic row and column sequences,
and color 6 is scattered corruption. The output removes all corruption and
restores every lattice intersection, including positions where the marker was
missing in the input.

Observed periods: pair 1 has marker 5 every 3 rows and 3 columns; pair 2 has
marker 3 every 2 rows and 2 columns; pair 3 has marker 3 every 4 rows and 3
columns. Both test inputs visibly support the same law (3x3 lattice of 8 on 4;
2x2 lattice of 1 on 4).

I implemented a general visible-only inference rather than hard-coding color 6
or phase zero. It chooses the most frequent color as background, then scores each
other color against all repeated Cartesian lattices using the F1 balance between
marker precision (candidate pixels on the lattice) and lattice occupancy
(observed marker pixels despite corruption). It requires at least two selected
rows and columns and at least three observed marker cells. Remaining uncertainty:
a tiny or extremely corrupted instance could underdetermine the period, but all
visible examples have ample support.
