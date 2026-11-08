"""BAND-DOCK concept family: tetris-dock scattered pieces into a jagged
band's bite, chaining per-column interlocks until the stack is a
completed rectangle.

Closes the 16b78196 eval-distribution hole (per eval_gap_rank): the
corpus has gravity/stacking tasks, but none where loose pieces must be
REASSEMBLED against a full-span band — the first piece filling an edge
bite exactly, each next piece meshing per-column with the stack surface
(no gaps), stopping when the surface is flat; decoy notches that fit no
piece stay open; pieces cross sides freely; vertical bands transpose.

The concept (never a copy of the eval task's pairs): built in reverse —
a solid rectangle is cut into interlocking pieces by jagged interfaces,
its band-side face carves a bite into the band, then the pieces are
scattered; the rule must re-dock them.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
