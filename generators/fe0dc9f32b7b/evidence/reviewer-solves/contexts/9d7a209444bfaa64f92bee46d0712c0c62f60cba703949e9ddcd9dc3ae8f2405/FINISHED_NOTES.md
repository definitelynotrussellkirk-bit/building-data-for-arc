# Solve notes

This is a human work log. I had already seen the task rule while reviewing the generator, so this is **not a blind solve**. After `prepare`, I restricted inspection to `solve/challenge.json` and based the implementation below on checks visible in those examples.

## Visible evidence and hypotheses

1. The nonzero, non-8 cells at the top of column 0 form an ordered palette. In training example 1, zeros inside the outer frame become 4 and zeros inside both nested frames become 1; the third palette color 9 is unused because there is no third valid depth.
2. Four-connected color-8 components are candidate rectangular frames. A component is accepted when its bounding box is at least 3 by 3 and its cell count equals the hollow rectangle perimeter `2*(height+width)-4`.
3. Training example 2 is the negative case: its inner color-8 object has a rectangular bounding box but extra interior bars, so it is overfilled and does not count. Only the clean outer frame contributes depth 1.
4. Training example 3 has three clean nested frames but only two palette colors. Depths 1 and 2 are filled with 1 and 5; the depth-3 center remains 0 rather than reusing/clamping the last color.
5. Only input zeros are recolored. Palette cells, frame cells, and zeros outside all accepted boxes stay unchanged.

## Implementation plan

- Find all 4-connected color-8 components.
- Retain components whose size equals their bounding-box perimeter.
- For every zero cell, count retained boxes that strictly contain it.
- Use palette entry `depth-1` when available; otherwise leave zero.

No deliberate negative revision was created because the first implementation directly expresses all three visible distinctions.
