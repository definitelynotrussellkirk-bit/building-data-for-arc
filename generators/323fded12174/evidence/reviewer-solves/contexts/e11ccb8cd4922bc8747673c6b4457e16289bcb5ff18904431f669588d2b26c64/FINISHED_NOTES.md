# Solve work log

Earlier exposure: **yes**. I repaired this task's generator before this solve, so
I already knew the general rule family. During this fresh solve I kept the
Racket authority, generator source, reference solutions, private labels, and
prior solve notes closed, and used only `challenge.json`.

## Revision 1

Across all three visible demonstrations, each output is a permutation of the
input rows with every row preserved byte-for-byte. Counting nonzero cells gives
strict descending output order in every example. The two full-palette rows are
particularly useful: sorting by dominant color frequency, mixedness, or color
count would order them differently, while total nonzero occupancy matches.

Implemented a stable descending sort by `sum(cell != 0 for cell in row)`. I
expect stable behavior to be correct if a future lesson includes ties, although
this generated episode has distinct occupancies. No reference material was
consulted during this solve.
