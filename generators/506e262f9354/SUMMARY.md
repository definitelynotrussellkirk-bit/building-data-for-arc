# 506e262f9354

A contiguous vertical source of color `7` identifies a source column and a
bottom row.  The selected Racket rule replaces the entire canvas with an
upward, canvas-clipped triangle: at row `r`, paint positions whose horizontal
distance from the source column is at most `bottom_row - r`.  Use `7` at even
horizontal distance and `8` at odd horizontal distance; write `0` everywhere
else.

The generator deliberately mixes two lesson profiles:

- **canonical core** — a row-zero source with no decoys, matching the visible
  canonical distribution;
- **teaching** — a vertically shifted source plus at least one non-`7` cell
  outside the triangle, which the output erases.

This distinguishes the selected rule from two shortcuts that fit every
canonical training pair: “triangle height equals source-line length” and
“preserve cells outside the transformed region.”  Exact observable controls
cover grid height/width, source length, source-column position, and decoy
count.

Kind: `per_puzzle`. Current version: `3.0.0`. Canonical rule hash:
`d19e95f77d58`.
