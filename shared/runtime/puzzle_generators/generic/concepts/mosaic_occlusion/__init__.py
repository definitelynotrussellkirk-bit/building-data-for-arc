"""MOSAIC-OCCLUSION concept family: recover the content hidden behind a
solid patch on an off-center mirror-symmetric mosaic.

Closes the 0934a4d8 eval-distribution hole (next least-covered eval task
per eval_gap_rank): the corpus has symmetry-completion tasks, but none
where (a) the mirror axes are OFF the grid center, (b) the occluder is a
solid rectangle of a reserved color, and (c) the OUTPUT is only the
recovered rectangle, not the repaired grid.

The concept (never a copy of the eval task's pairs): a dense multi-color
mosaic is mirror-symmetric about one vertical and one horizontal axis,
both offset from the grid center (reflections c -> al - c, r -> au - r,
partially out of bounds). A solid rectangle of 8s occludes part of it.
The transform finds each axis as the largest conflict-free reflection
overlap on visible cells and outputs the occluded rectangle's hidden
content, each cell recovered from its first visible mirror image.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
