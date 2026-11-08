# 6b694a414d96 — paint rooms one door from the seed

A closed 2-D lattice of rectangular rooms is separated by color-1 or color-9
walls. Color-7 door cells connect the rooms on their opposite sides, and exactly
one room contains a color-2 seed. Preserve walls and doors, clear all rooms, and
paint color 8 only into the seed room's direct graph neighbors.

Generator version `3.0.0` replaces the former one-row strip sampler with
canonical-compatible 2-D lattices. Its three-example cyclic curriculum includes
horizontal adjacency, vertical adjacency, and a guaranteed second-hop room, so
complete lessons refute both orientation-only rules and the canonical-fitting
transitive-closure shortcut.

Portable regression coverage is under `tests/`. The reusable
`workspace/room_graph_probe.py` verifies canonical parity, complete schedule
windows, generated validity, declared shortcut fit, and finite-rival lesson
identifiability against the selected source bytes. The canonical Racket rule is
unchanged with normalized hash `bf24da6609f2`.

Approval is derived by maintainer verification, not by this summary.
