# a452b4b4f04a — Complete the Rectangle

**Input-only generator, version 3.0.0.** A zero-background 6–20 by 6–20 grid
contains 1–3 distinct colors from 1–9. Each color marks either two opposite
corners, any three corners, or all four corners of a rectangle at least 3 by 3.
Entire bounding boxes are disjoint. The canonical Racket rule completes each
color's hollow rectangle perimeter; it remains the label authority.

The default three-phase curriculum contains a single-color/three-corner
canonical component, a multicolor component, and a two-corner/boundary component.
Every three consecutive default examples cover all three components. Exact
`grid_h`, `grid_w`, `n_colors`, and `corner_count` overrides intentionally take
precedence over that curriculum. Unknown and retired controls raise errors.

Rule pin: `f54dbee03c8b`. Selected active Racket source was synchronized to
canonical by removing one explanatory comment only. No executable rule form,
canonical grid, or canonical program changed.

Final qualification: 12/12 battery stages green, all 5 canonical pairs accepted,
1,800 default Racket cases, 243 Racket exact-control cases, and 480 assembled
lessons. These certify only the measured inputs and three declared rivals;
they do not establish universal induction or model-training benefit. Training
approval is unchanged. See `notes.md` and `workspace/README.md` for evidence and
reproduction. Task-local tests must be run explicitly; they are not collected by
the repository's default test path.
