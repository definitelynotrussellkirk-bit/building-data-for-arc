# 4e79c276ce9d

A zero-background grid contains four monochrome, orthogonally connected objects. Select the uniquely smallest component by **cell count**, crop its exact occupied shape to its bounding box, and translate that crop to the origin. Same-color regions that touch only diagonally remain separate; different colors remain separate even when edge-adjacent.

Version 4.0.0 uses a six-position curriculum with three demonstrations. Every default input matches one of the canonical `(height, width, palette-size)` profiles. Four of every six positions are counterexample-rich scenes that distinguish cell count from bounding-box area, solid-box output, total color frequency, whole-color buckets, eight-connectivity, multicolor connectivity, and reading-order selection. Exact controls are limited to `grid_h` 9–12 and `grid_w` 10–13.

Kind: `per_puzzle`. Approval is derived by the catalog from current code and retained evidence.

Current accepted generator version: `4.0.0`. The selected source/rule approval is reviewer-reported; finite test and curriculum claims are in its task-owned notes.
