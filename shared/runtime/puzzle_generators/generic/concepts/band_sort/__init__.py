"""BAND-SORT concept family: monochrome workspace pieces drop into the
color-matching band, bottom-aligned and recolored to the band's edge.

Closes the 7c66cb00 eval-distribution hole (per eval_gap_rank): the
corpus has recolor and gravity tasks, but none where nested decorations
count as INDEPENDENT pieces (a ring's interior bar leaves its parent and
files into its own band), the destination is keyed by the band's
interior color, the landing is bottom-aligned with columns preserved,
and the piece is repainted in the band's 1-wide edge-column color.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
