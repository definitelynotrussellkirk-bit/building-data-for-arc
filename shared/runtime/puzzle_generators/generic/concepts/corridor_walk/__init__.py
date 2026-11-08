"""CORRIDOR-WALK concept family: pattern-painted walks through terrain
corridors with turn markers.

Closes the 195c6913 eval-distribution hole (the last of the second
eval_gap_rank tier): the corpus has path tasks, but none where a legend
row of 2x2 swatches defines a repeating PATH PATTERN, another 2x2 gives
the TURN-MARKER color, and single border cells launch walks through the
corridor terrain — painting the pattern cell by cell, stamping the
marker color on the abandoned straight-ahead cell at every turn, turning
into the perpendicular corridor run of length >= 2 (longest wins), and
stopping at dead ends or the grid edge. Legend and marker squares
dissolve into their surrounding terrain.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
