"""GLYPH-SWAP concept family: boxed solid squares become sample glyphs in
legend-mapped colors.

Closes the edb79dae eval-distribution hole (per eval_gap_rank): the
corpus has recolor-map tasks, but none reading the map from TWO-COLOR
legend chunks (source touching target), the glyph shapes from loose
single-color samples, and applying both inside a framed box — each solid
square replaced by its color's glyph repainted in the mapped color, with
the box (frame included) as the answer.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
