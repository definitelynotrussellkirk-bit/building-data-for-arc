# 17ea562973ac — Draw the Missing Box

A lawful input is a 6..12 by 7..14 zero-background grid containing exactly 2..8 cells of one color from 2..9. The cells' minimal bounding rectangle spans at least four rows and four columns. Return a fresh grid of the same size with only that rectangle's border painted in the marker color; all source markers, including interior markers, are otherwise cleared.

The four live exact controls are `grid_h`, `grid_w`, `color`, and `num_cells`. Every declared value is valid in every difficulty band and is recoverable from the returned pixels. Scheduled lessons include two-marker cases, interior markers, and cases where the first two markers do not determine the complete box.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule pin: `22bfb52d3f48`.
