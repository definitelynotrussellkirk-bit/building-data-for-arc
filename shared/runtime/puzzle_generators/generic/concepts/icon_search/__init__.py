"""ICON-SEARCH concept family: an icon word-search with a verdict strip.

Closes the d8e07eb2 eval-distribution hole (per eval_gap_rank): the
corpus has matching/highlighting tasks, but none with this three-panel
report layout — a QUERY strip of 3x3 icons above a separator, an icon
board on a 5-cell pitch, and a VERDICT strip below a second separator.

The concept (never a copy of the eval task's pairs): if the query icons'
exact matches fill one whole board row or column, the query strip is
green-lit, that line is band-highlighted, and the verdict strip turns
green; additionally the query icon at position = line index is swapped
for the icon BELOW its match (wrapping) unless that icon already appears
in the query (both eval success trains pin this sub-rule). Otherwise
each individual match is boxed and the verdict strip turns red.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
