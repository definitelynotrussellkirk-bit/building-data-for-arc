# 7071285d78ce — local object transpose

On a zero background, independently transpose each same-color, four-connected
object about its own bounding-box top-left. For a cell `(r,c)` in an object
anchored at `(r0,c0)`, paint its original color at
`(r0 + c - c0, c0 + r - r0)` on a **blank output grid** of the original size.
This blank-output detail permits an object's destination to overlap another
object's original footprint without erasing the transposed result.

Version `3.0.0` generates exact `8..14` row and column sizes, `2..4` orthogonally
separated objects, and distinct foreground colors. Each object has three to
five cells, is nonrectangular, and changes under transpose. Destinations remain
in bounds and pairwise disjoint. Count and palette aliases are exact and
conflicts are explicit. Default, warm, cool, and mixed palettes are supported.

A period-two curriculum alternates canonical `3x2` tetromino objects with broad
examples containing both a three-cell object and an asymmetric width-four
pentomino. The intended lesson uses three demonstrations and one query from
four consecutive draws, with every single-query holdout checked against the
declared rivals. Exact overrides take precedence over profile defaults.

Kind: `per_puzzle`. Selected Racket rule: `9eb76f1bb8b7`, unchanged.
See `notes.md` for current design decisions, measured limits, and retained audit
status. Approval is derived by the catalog from current code and retained evidence.
