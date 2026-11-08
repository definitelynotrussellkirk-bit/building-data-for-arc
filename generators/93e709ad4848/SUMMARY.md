# 93e709ad4848 — Nearest-Corner Dock

Generate one monochromatic 4-connected object on a zero background. The unchanged
Racket rule translates its tight crop to the nearest legal corner placement,
using the bounding-box center. Equal distances choose top, then left. Shape,
holes, foreground color, orientation and canvas dimensions are preserved.

Version 3.0.0 replaces the imported, unrelated touch-degree recoloring sampler.
The default three-profile curriculum covers midpoint-crossing shapes, exact ties,
and unequal canvas dimensions. A seed-stable rectangular shape family ensures
that a ring query has a ring demonstration in any consecutive three-demo lesson.
Five shape families, their orientations, all nine foreground colors, and exact
6..24 dimension controls are available. The semantic validator intentionally
accepts a broader lawful one-object domain than the finite sampling family.

See `notes.md`, task-local tests and `workspace/` for contracts, probes and limits.
Approval remains unchanged; a generic minimal-shape lint warning requires a
maintainer disposition or a shared-tool fix followed by a new candidate check.
