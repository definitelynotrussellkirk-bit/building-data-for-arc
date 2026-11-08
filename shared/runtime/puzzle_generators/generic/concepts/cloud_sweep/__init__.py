"""CLOUD-SWEEP concept family: a yellow edge bar marches through a cloudy
field, clearing its channel, stamping every 2 rows, with every 3rd stamp
green and cloud-run-painting.

Closes the 221dfab4 eval-distribution hole (per eval_gap_rank): the
corpus has ray/periodic-stamp tasks, but none combining a swept CLEAR
channel (all cloud cells in the bar's columns erased along the whole
path), a 2-row stamp cadence, a modulo-3 color alternation, and a green
stamp that additionally paints every maximal cloud RUN in its row.

The concept (never a copy of the eval task's pairs): a 4-colored bar on
the top or bottom edge; direction = away from its edge; stamps at
r0 +/- 2k; stamp k is green when k = 2 (mod 3); background and cloud
colors vary per pair.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
