# fe0dc9f32b7b — Nested Palette Fill

Column 0 contains a contiguous top-to-bottom palette of two or three distinct colors excluding 0 and 8. Column 1 is a zero gap. The body contains one nested color-8 chain in one of four calibrated forms:

- two clean hollow frames;
- one clean outer frame around a qualifying inner component made by moving one perimeter cell inward;
- one clean outer frame around an overfilled, non-qualifying color-8 component;
- three clean hollow frames.

A color-8 component qualifies when its bounding box is at least 3×3 and its component size equals that box's perimeter. Exact perimeter occupancy is **not** required. For each input zero, count qualifying boxes that strictly contain it and use `palette[depth-1]`; cells deeper than the palette length remain zero. Overfilled lookalikes do not count.

Version `3.1.0`; canonical `RULE_HASH = 5f1e925f80ea`. Ordinary three-sample windows cycle through size-equals-perimeter/nested-depth, malformed-object-filter, and palette-exhaustion lessons. Exact observable axes are `grid_h`, `grid_w`, `palette_size`, and `scene_kind`.

The non-hollow positive branch intentionally uses one-cell inward swaps in eight safe local orientations. This directly refutes an exact-outline shortcut but does not cover every connected equal-count topology accepted by the authority.
