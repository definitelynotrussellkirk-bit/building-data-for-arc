# Current design and implementation

Parent `981571dc` is a dense 30×30 table with erased cells represented by zero.
The completed table is invariant under transpose and under independent row/column
suffix mirrors that leave indices 0 and 1 fixed and pair every later index with
`n+1-i`.  The canonical program is deliberately two-stage: first repair visible
transpose partners; then use that intermediate to close the remaining suffix-
mirror holes.  This reproduces all four supplied demonstrations and the private
public-evaluation gold.

The native parameter is `completion_depth`: `closure` is the exact canonical
program, while `transpose_only` stops after the first stage.  Generated inputs
are matched across settings, contain direct and multi-hop erasures, and include
five mandatory mask patterns that distinguish transpose, row-mirror,
column-mirror, double-mirror, and true A→B-dependent completion.  The first two
demonstrations are bounded-search checked against the opposite setting and ten
additional executable shortcuts.  Four queries are always materialized; the
last is a dense 30×30 stress case.

A produces a transpose-repaired grid.  B consumes that grid, not the original:
the retained chain mask erases a target and all three of its original suffix-
mirror donors while leaving the transpose partners of those donors visible.
Replacing B's source with the original input therefore changes the final label.

This is unapproved authoring work.  Owner registration, exact-source review,
native qualification/acceptance, and any training admission remain pending.
Finite rival checks do not establish universal rule uniqueness.
