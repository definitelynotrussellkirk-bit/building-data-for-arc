# Solve work log

## Exposure record

Earlier rule exposure: **yes**. This is the required post-repair visible-only solve, not a blind solve. After the current challenge was prepared, I kept the selected generator, its Racket authority, private labels, and prior solve archive closed. I used only the displayed train pairs and my own implementation.

## Hypothesis from the three train pairs

The grid dimensions and occupied cells are preserved. Each 4-connected green component is recolored independently according to its orthogonal adjacency graph:

1. If any component cell has exactly three orthogonal neighbors, recolor the whole component red (2).
2. Otherwise count cells with exactly two perpendicular neighbors (turns/corners). If the count is exactly two, recolor the component magenta (6).
3. Otherwise recolor it blue (1).

The demonstrations include straight/ordinary paths, exactly-two-turn paths, T-junctions, degree-four junctions, and longer paths. In particular, a four-way junction remains blue rather than being treated as a T-junction, and the corner criterion is exact rather than a lower bound.

## Implementation and stopping reason

`solution.py` extracts color-3 components by flood fill, computes local degree and perpendicular-turn counts, and writes the component color without changing any background cell. This one hypothesis explains every visible output cell; no competing hypothesis remained after checking the degree-four and exact-two-corner cases.
