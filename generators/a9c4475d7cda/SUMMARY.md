# a9c4475d7cda

Two full color-8 rows and two full color-8 columns divide a 9×9..17×17 background-0 grid into nine panels. Each panel contains a controlled number of color-6 cells. The output is a 3×3 binary mask whose entry is 1 iff the corresponding panel contains **at least two** color-6 cells.

Selected version: `3.0.0`. Canonical rule hash: `8cfb5cf9c2c4`.

Exact public controls are `grid_h`, `grid_w`, and `count_profile`. The four profiles (`canonical_bridge`, `balanced`, `sparse`, `dense`) all contain count-1, count-2, and count-3 panels, so generated lessons distinguish the intended threshold from both `count == 2` and `count > 0` rivals. Structural validation, override observation, a Python rule mirror, executable witnesses/rivals, and task-local regression tests are included in the selected implementation.

Final reviewed generator SHA-256: `1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51`.
