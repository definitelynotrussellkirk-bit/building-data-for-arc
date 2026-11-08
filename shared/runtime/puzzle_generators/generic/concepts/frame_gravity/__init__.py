"""FRAME-GRAVITY concept family: framed pieces slide left or right by
frame color, in independent lanes.

Closes the b5ca7ac4 eval-distribution hole (per eval_gap_rank): the
corpus has gravity tasks, but none where the DIRECTION is keyed by the
piece's frame color (cyan frames slide left, red frames slide right),
rows are preserved, stacking happens only against same-direction pieces
(opposite lanes pass through each other — the eval trains falsify a
shared-occupancy simulation), and pieces settle edge-first.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
