"""SEQUENCE-WINDOW concept family: extrapolate a shape progression into a
gray-bracket-marked window.

Closes the 20a9e565 eval-distribution hole (the last of the nine
least-covered eval tasks per eval_gap_rank, and the hardest): shapes form
a progression along one axis — constant gap, affine widths/heights, a
common top/bottom/center anchor line, colors repeating in a cycle — and
two gray corner brackets frame a window over a MISSING element (beyond
the last shape or before the first). The output is that window's
extrapolated content.

The rule reads each column-offset's content along the anchor-distance
axis from the deepest donor shape and extends it by: shortest verified
period, else a phase-shift onto a longer column, else full-block
repetition; per-column support extents extrapolate affinely (same-parity
fallback when they zigzag); single-colored shapes recolor by the observed
color cycle. Vertical progressions are handled by transposing in and out.
At 3656 grammar tokens this is the largest verified rule in the corpus.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
