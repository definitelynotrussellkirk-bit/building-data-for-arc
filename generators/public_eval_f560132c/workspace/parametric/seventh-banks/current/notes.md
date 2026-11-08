# Public parent f560132c — authoring design

The input contains four or nine disconnected jigsaw pieces. One multicolor
piece embeds a 2×2 or 3×3 palette; a zero palette cell is still part of that
piece's silhouette. Keep that palette-bearing piece unrotated at the output's
top-left, rotate the other pieces by quarter turns, and exactly tile the square
whose area is the sum of all piece areas. Recolor each placed piece by the
palette position it occupies: corners for 2×2; corners, ordered side pieces and
the remaining interior piece for 3×3.

The default `pack_only` rule is the public parent. The alternative
`highlight_hub` first builds the complete piece-id tiling, derives the
four-neighbor adjacency graph, selects the unique maximum-degree piece, and
recolors that packed region to 1. `highlight_largest` is retained as the wrong-
intermediate counterfactual. Generated palettes exclude 1 and lessons ensure
the adjacency hub is not the largest-area piece.

This is unapproved authoring work. Owner registration, exact-source review,
native qualification, acceptance and any training admission remain pending.
