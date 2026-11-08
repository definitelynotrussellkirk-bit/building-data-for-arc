# Post-repair solve notes

This is a human work log from the visible examples. I had already inspected the assigned generator and selected rule during repair, so this episode is **not blind**; I kept those sources closed after `solve_episode.py prepare` and used no reference solution or private labels during this solve.

## Hypothesis

- Read the contiguous nonzero prefix of column 0 as an outer-to-inner fill palette.
- Treat each 4-connected color-8 component as a candidate box. A component qualifies when its bounding box is at least 3×3 and its cell count equals that bounding box's perimeter, `2(h+w)-4`.
- For each zero cell, count qualifying bounding boxes that strictly contain it. Fill depth 1 with the first palette color, depth 2 with the second, and so on. Leave cells deeper than the palette length zero; preserve all existing nonzero cells.

## Visible evidence

- The first demonstration contains an inner color-8 component whose cells are not an exact rectangular outline, yet its bounding box is still treated as a nesting boundary. Its count matches the box perimeter, distinguishing the inferred predicate from an outline-only shortcut.
- The second demonstration contains a color-8 lookalike that does not meet the qualifying count and therefore does not add depth.
- The third demonstration has more nested boxes than palette entries; the unmatched deepest region remains zero rather than reusing or clamping the final color.

I implemented this rule directly and stopped after the first genuine solution revision if all visible pairs passed.
