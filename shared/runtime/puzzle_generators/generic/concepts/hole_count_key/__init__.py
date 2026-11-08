"""HOLE-COUNT-KEY concept family: a legend of hole-pierced rectangle keys
recolors gray field blobs by their enclosed-hole count.

Closes the e3721c99 eval-distribution hole (next least-covered eval task
per eval_gap_rank): the corpus has recolor-by-property tasks, but none
where the color MAP itself is read off legend objects, keyed by the count
of enclosed holes, with unmatched blobs erased.

The concept (never a copy of the eval task's pairs): legend keys are solid
rectangles (cells + enclosed holes fill their bbox, both sides >= 2) in
any non-gray color, each pierced by 0..n single-cell holes — hole-count ->
key color. Every gray blob in the field is recolored by the key matching
its own enclosed-hole count; blobs with no matching key are erased. The
separator stripe (1-wide or L-shaped, never bbox-filling) and the keys
stay unchanged. The stripe may share the color of a key (the eval task
does exactly this) — the rectangle test, not color, tells them apart.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
