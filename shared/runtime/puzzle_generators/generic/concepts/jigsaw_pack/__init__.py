"""JIGSAW-PACK concept family: loose pieces exactly tile a silhouette blob
on the other side of the grid.

Closes the 5dbc8537 eval-distribution hole (per eval_gap_rank): the
corpus has stacking and overlay tasks, but no exact-cover JIGSAW — one
side of the grid holds a single silhouette blob, the other a set of
loose (possibly multicolor) pieces that tile it exactly under
translation only; the answer is the blob's bounding box padded by 1,
with the blob replaced by the solved tiling.

The rule detects the two sides by corner-line backgrounds + an
argmax-scored split, then solves the exact tiling by backtracking (the
first empty blob cell must be covered by some piece's own first cell).

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
