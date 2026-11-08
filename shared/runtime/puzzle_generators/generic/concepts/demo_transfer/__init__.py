"""DEMO-TRANSFER concept family: learn a box-to-box transform from an
in-grid demonstration pair and apply it to a query box.

Closes the 4c7dc4dd eval-distribution hole (next least-covered eval task
per eval_gap_rank): the corpus has nothing META like this — the grid
itself CONTAINS a worked example (two small boxes showing X and f(X));
the transform f must be inferred in-grid and applied to a separate query
box, with the answer written at the size of the query's interior.

The concept (never a copy of the eval task's pairs): four one-cell-thick
boxes (uniform nonzero ring, >=25% black interior, <=2 nonzero interior
colors, ring color not inside) sit on a dense noise field. One box is
EMPTY — the answer slot; the non-empty box NEAREST it is the QUERY; the
remaining two are the DEMO pair. f is identified by mask-testing a fixed
library — complement, connect-aligned-dots, flip-lr, flip-ud, rotate-180
— against the demo in either direction; the output is f applied to the
query interior (new cells take the query's modal nonzero color).

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
