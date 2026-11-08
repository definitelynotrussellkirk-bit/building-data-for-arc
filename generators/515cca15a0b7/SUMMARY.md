# 515cca15a0b7

Version `2.1.0`. The background is 0. Treat each same-color 4-connected
foreground component independently. Keep a component exactly when it touches at
least one horizontal border (top or bottom) **and** at least one vertical border
(left or right); erase components touching only one axis or neither. A survivor
need not include a literal corner cell.

The production sampler uses four constructive layout roles on a five-position
schedule:

`canonical_mix, dense, canonical_mix, edge_contrast, kept_variety`

This gives 40% canonical-profile support and guarantees that every cyclic
three-example window contains both (1) an extended survivor that touches two
border axes without occupying a corner and (2) disconnected same-color
horizontal-only and vertical-only components that must both be erased. Exact
public controls are `grid_h` (8..10), `grid_w` (9..11), and `layout`.

The selected Racket authority remains canonical rule hash `8a3c35320856`; this
repair changes only the generator, task-local tests, and workspace probes.
