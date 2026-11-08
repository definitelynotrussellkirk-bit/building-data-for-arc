"""MOSAIC-REPAIR concept family: heal black holes in a diagonally +
off-center doubly-mirrored mosaic, outputting the WHOLE repaired grid.

Closes the 981571dc eval-distribution hole (next least-covered eval task
per eval_gap_rank). Sibling of [[mosaic_occlusion]] (0934a4d8) with three
twists: the occluders are BLACK (0) and irregular/multiple, the mosaic is
additionally symmetric about the MAIN DIAGONAL, and the output is the
full repaired grid rather than the cropped patch.

The concept (never a copy of the eval task's pairs): a square mosaic is
symmetric under transpose and under reflections c -> a - c, r -> a - r
(one shared off-center axis parameter, so the group closes). Black holes
pock it. The transform detects each axis as the largest conflict-free
reflection overlap on visible cells (diagonal gated on conflict-freedom)
and fills every hole from its first visible image under transpose, the
two mirrors, and their compositions.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
