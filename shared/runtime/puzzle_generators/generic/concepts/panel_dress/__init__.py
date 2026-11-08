"""PANEL-DRESS concept family: solid panels take the isolated shape whose
enclosed-hole count matches their dot count.

Closes the 8698868d eval-distribution hole (per eval_gap_rank): the
corpus has count-keyed recolor tasks, but none where PANELS tiling a
block (identified purely by touching each other) are keyed by their
field-colored dot count to loose hole-bearing shapes, and the answer is
the panel block re-rendered — panels refilled solid, each shape pasted
centered with its holes showing the panel color.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
