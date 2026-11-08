# Post-repair solve notes

## Evidence used

Only the visible `solve/challenge.json` train pairs and queries were used after preparation. I had already inspected the generator and canonical rule while doing the assigned repair, so this is intentionally recorded as an exposed solve, not a blind solve.

## Hypothesis

Each input has a dominant background, exactly two endpoint dots, several long parallel wall stripes, and a short three-cell marker run embedded in every wall. The output preserves the scene and paints an endpoint-colored orthogonal route from the first endpoint to the second. In the orientation where walls are horizontal, the route:

1. descends from the upper endpoint;
2. one row before each wall, turns horizontally to the **middle** marker cell;
3. changes that middle marker cell to the endpoint color and continues below the wall;
4. after the final wall, reaches the lower endpoint row and hooks horizontally to it.

Vertical-wall examples are the transpose of the same process. The middle-cell choice is supported by every visible wall crossing: the center marker changes color while the two outer marker cells remain.

## Implementation choices

- Infer semantic colors by count: background is most common, endpoints are the color occurring exactly twice, and the more frequent of the two remaining colors is the wall color.
- Infer orientation from whether wall-color cells concentrate more strongly by row or by column.
- Transpose vertical cases, solve one horizontal normal form, then transpose back.
- Preserve every cell except those on the added route.

## Alternatives rejected

- Connecting endpoints directly ignores the wall markers and fails all visible outputs.
- Passing through the leftmost or rightmost marker fits no visible crossing; the center is consistently selected.
- Treating each wall independently without carrying forward the previous marker column misses the staircase segments between walls.
