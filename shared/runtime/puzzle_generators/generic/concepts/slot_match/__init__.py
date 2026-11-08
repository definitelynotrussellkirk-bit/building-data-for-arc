"""SLOT-MATCH concept family: fill a template's shape-slots with the modal
color of matching scattered shapes.

Closes the 67e490f4 eval-distribution hole (next least-covered eval task
per eval_gap_rank): the corpus has extraction and recolor tasks, but none
where a large template board is pierced by background-colored SLOTS whose
fill color must be voted from scattered shapes of the same shape CLASS
(matching up to rotation/reflection, majority color wins).

The concept (never a copy of the eval task's pairs): the biggest object
is a solid rectangle (the template) pierced by slots of the field's
background color; small shapes lie scattered outside its bounding box in
several colors per shape class, one color strictly most frequent. The
output is the template's bounding box with every slot recolored to its
class's modal color.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
