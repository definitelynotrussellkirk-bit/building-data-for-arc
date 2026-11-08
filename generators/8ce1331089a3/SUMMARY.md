# 8ce1331089a3

A rectangular grid has four distinct nonzero border colors: top, bottom,
left, and right. Corners are zero. Sparse interior pixels are separated from
the border by one blank cell. Pixels whose colors match a border move to the
adjacent inner wall for that border while preserving the perpendicular
coordinate. One-off interior colors that match no border are distractors and
are removed.

The reviewed generator cycles the four canonical `(height, width,
palette-size, interior-pixel-count)` profiles:

- `(12, 12, 7, 7)`
- `(10, 15, 6, 7)`
- `(14, 11, 6, 6)`
- `(14, 17, 8, 13)`

Every sample contains all decisive teaching evidence: at least three routes,
1–3 removable non-border distractors, and a repeated matching route so that a
"move only the first pixel per color" shortcut fails. Difficulty changes the
route-balance/placement curriculum without changing canonical profile
support. All four declared axes are exact, observable overrides.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Rule pin:
`3f9dcd988189`.
