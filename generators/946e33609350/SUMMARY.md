# 946e33609350 — Fill by nearest seed through corridors

A color-1 frame and optional one-gap interior barrier define the traversable
corridors. Every other non-zero cell is a distinct singleton seed. Each zero
cell takes the color of its unique nearest seed under four-neighbor shortest
path distance through non-wall cells; finite equal-distance ties remain zero.
Walls and seeds are preserved.

Generator version: `3.0.0`. Canonical rule hash: `1ec8459f97ec`.

The production lesson uses three demonstrations in a cyclic semantic schedule:
`horizontal_gate`, `open_tie`, and `vertical_gate`. Together they distinguish
wall-aware distance, tie preservation, and participation of all three seeds.
Public overrides are exact for height `6..10`, width `9..12`, seed count `2..3`,
and the three profiles. The selected Racket authority was not changed.

Approval and training admission remain catalog decisions; passing reviewer
checks does not itself admit generated lessons to training.
