# b2d6e6b60917

A 21×21 zero-background grid contains one unique-largest monochrome source
template and two or three smaller monochrome marker fragments. Each marker is a
proper subset of the source translated into the first slot of one of eight rays.
Infer its direction relative to the source, then repeat the full source shape
outward in the marker color. Active row and column strides are the source
bounding-box height/width plus one, and existing cells are preserved.

The reviewed curriculum cycles through 3×3, 2×4, and 4×2 source bounding boxes.
Every three-example lesson therefore retains literal canonical anchors while
refuting the fixed-stride-4 shortcut that fits all canonical pairs.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash:
`73b1bc28244d`.

The canonical generator was unchanged in this review. A separate task-local
proposal adds `template = full | fragment`: the default repeats the full source,
while the alternate repeats only the marker-recovered source fragment. The
finite family is proposed, not owner-qualified, accepted, or training-admitted.
