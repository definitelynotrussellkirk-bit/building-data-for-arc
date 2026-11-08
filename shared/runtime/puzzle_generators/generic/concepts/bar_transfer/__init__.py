"""BAR-TRANSFER concept family: a red/green bar legend moves one tower's
icon count onto another.

Closes the 9aaea919 eval-distribution hole (next least-covered eval task
per eval_gap_rank): the corpus has counting and stacking tasks, but none
where a bottom-row bar LEGEND designates a source tower (red) whose icon
count is transferred onto a destination tower (green), with the source
graying out.

The concept (never a copy of the eval task's pairs): towers of identical
icons stand in separate column slots over a bottom-row legend containing
exactly one GREEN (3) and one RED (2) bar, each 1 row tall on the last
row. The red-bar tower's icon count transfers to the green-bar tower —
that many copies of the green tower's icon are stacked on top of it at
the tower's vertical pitch (icon height + 1); the red-bar tower is
recolored gray (5); both bars vanish; barless towers stay untouched.
Bars are identified by their bottom-row position, NOT color — towers may
themselves be red or green (the eval task does exactly this).

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
