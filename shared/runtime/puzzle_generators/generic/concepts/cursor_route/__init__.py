"""CURSOR-ROUTE concept family: header-programmed cursor excursions with
bounce runs.

Closes the e87109e9 eval-distribution hole (per eval_gap_rank): the
corpus has ray and path tasks, but nothing PROGRAMMED — a header strip
of boxes gives a target-color sequence with a turn hand per box (bar
left of the box = turn left, right = turn right); a 2x2 cursor sends one
excursion per box from its home: a straight leg to the axis-aligned
target, the hand turn on arrival, then a run that BOUNCES off blocking
rects (sliding toward the blocker's farther extension) until a grid
edge. Absent or non-aligned targets send the cursor straight up toward
the header. The answer is the field with the cyan trail painted.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
