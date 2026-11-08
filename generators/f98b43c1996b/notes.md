# Working notes: f98b43c1996b

## Current decision

Keep the frozen canonical rule as the exact default. The admitted nearby variant performs canonical 2x2 diagonalization first, then selects the unique most frequent surviving nonzero color and recolors it to 8.

The teaching construction intentionally makes source color 2 lead before Step A and color 5 lead afterward; this defeats ranking the source grid, numeric extrema, row-major-first, and highlight-all shortcuts at the two-demo minimum. The protected witness uses source-frequency ranking as a wrong intermediate and changes nine final cells.

Status: reviewer-ready authoring preflight only. Owner exact-source qualification/acceptance and any training admission remain pending.
