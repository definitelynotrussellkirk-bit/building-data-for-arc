"""CHAIN-BRIDGE concept family: a color-sequence strip wires framed boxes
together with core-band bridges.

Closes the 3e6067c3 eval-distribution hole (per eval_gap_rank): the
corpus has connect-the-dots tasks, but none where the CONNECTION ORDER
is spelled out by a legend strip — consecutive entries name boxes
(duplicate core colors resolved by backtracking a non-revisiting walk in
which consecutive boxes must face each other across a clear gap), each
pair joined by a bridge through the gap along the earlier box's core
band, painted in the earlier entry's color.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
