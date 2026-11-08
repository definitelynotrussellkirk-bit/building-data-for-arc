"""CHECKER-RAYS concept family: checkerboard fields with diamond rings and
flanking diagonal segments that fire perpendicular rays.

Closes the single largest eval-distribution hole (80a900e0 sat 6.4 sigma
from every corpus generator per eval_gap_rank): the corpus never produced
CHECKERBOARD backgrounds, nor the free-end-fires-perpendicular-ray concept.

The concept (never a copy of the eval task's pairs): the background is a
two-color checkerboard (the two most frequent colors). Foreground colors
form diagonal chains — closed diamond RINGS (every cell has two same-color
diagonal neighbors) and open SEGMENTS hugging the ring sides. Every free
end (exactly one same-color diagonal neighbor) fires rays perpendicular to
its chain, in each diagonal direction whose adjacent cell is background,
painting over the checkerboard until a shape or the edge stops it. Rings
have no free ends, so they never fire.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
