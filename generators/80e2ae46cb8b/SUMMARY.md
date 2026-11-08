# 80e2ae46cb8b

Grid formed by REPEATING A SMALLER TILE — choose AXIS ∈ {horizontal, vertical}, PERIOD ∈ {2..5} (tile width or height along the repeating axis), REPEAT ∈ {2..4} (number of copies), and OTHER_DIM ∈ {3..7} (perpendicular dimension). The source TILE is filled with a 3-color palette (warm/cool/broad/primary) at random per-cell, with anchor cells (top-left and one opposite corner) constrained to specific palette colors. The full grid = tile repeated REPEAT times along AXIS. Rule (REMOVE ONE REPEATED PERIOD ALONG THE AXIS): detect the axis-aligned PERIOD P (the repeating unit) and the REPEAT COUNT R. Output is the input with ONE FULL PERIOD removed — i.e., the tile repeated R-1 times along the same axis. If horizontal: output width = (R-1) * P. If vertical: output height = (R-1) * P. Net: one tile is stripped off the repeating sequence.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
