# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private labels,
or prior solve notes. Before the blind preparation I had only read packet-level workflow
documentation and the assignment identifiers.

## Revision 1 — Cartesian intersections from visible markers

Across all three visible examples, the cells changed from background `0` to `3` are
exactly the Cartesian product of:

- every row containing a `1`, and
- every column containing a `2` in the first row.

Other `2` cells away from the first row are distractors, and the two cells in the
remaining nonzero color (`5` in the examples) are untouched distractors. All original
nonzero cells are preserved. This preservation matters for query 0, where each `1`
occupies column 0 and column 0 is also selected by a first-row `2`; I leave those `1`
cells unchanged rather than overwriting them with `3`.

Implemented a shape-preserving copy, collected selected rows and columns, and wrote `3`
only into zero-valued intersections. Remaining uncertainty is limited to the collision
policy because no visible training example places a row marker directly at a selected
intersection; preserving original nonzero cells is consistent with every demonstrated
change and the apparent overlay operation.
