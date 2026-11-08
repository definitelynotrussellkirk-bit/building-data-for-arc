"""TILE-BLUEPRINT concept family: a lattice of repeated tiles where a few
anomalous tiles are a partial rendering of a blueprint that must be completed.

Closes the b99e7126 eval-distribution hole (next least-covered task after
80a900e0 per eval_gap_rank): the corpus never produced separator-lattice
fields whose anomaly is itself a picture AT TILE SCALE.

The concept (never a copy of the eval task's pairs): a separator-color grid
of lines divides the field into an nr x nc lattice of th x tw tiles, all
carrying one NORMAL motif. A few tiles instead carry an ANOMALOUS motif that
introduces a NOVEL color (absent from the normal motif and the separator).
The novel color's cell mask inside the anomalous motif is a BLUEPRINT at
tile scale: the input's anomalous tiles render part of it; the output
completes it — every blueprint tile position gets the anomalous motif, all
other tiles the normal motif.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
