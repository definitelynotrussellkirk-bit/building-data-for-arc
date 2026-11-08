# Native parametric family: linked-color projection

`projection_mode=local_cells` is the exact selected canonical program: retain a
cell only when that cell has a same-color cardinal neighbor.

`projection_mode=linked_colors` is a sequential alternative. Step A scans the
input and derives the set of colors that occur in at least one same-color
cardinal link. Step B consumes that set in a separate whole-grid projection,
retaining every occurrence of those colors, including remote singleton cells.
The generated grammar always contains remote occurrences, diagonal decoys, and
different-color contacts, so every visible demonstration distinguishes the two
settings. The fourth query is a substantive 30x30 boundary case.

The adapter is deterministic, uses local RNG instances, supports 2–6 demos and
exactly four private queries, and shares identical inputs across settings.
