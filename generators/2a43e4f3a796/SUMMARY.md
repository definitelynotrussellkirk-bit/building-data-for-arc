# 2a43e4f3a796

Compact each column's nonzero cells to the bottom while preserving every value,
its multiplicity, and its top-to-bottom order. Fill the vacated upper cells with
zero. Zero remains background even when another color is more frequent; gray
`5` moves like every other foreground color.

Kind: `per_puzzle`. Selected generator version: `3.1.0`.
Canonical rule hash: `7b698fc27b90` (unchanged).

Ordinary sampling uses the period-five cycle dense teaching, sparse teaching,
dense teaching, sparse teaching, free. Teaching inputs contain a gapped column
with at least six cells; free draws cap columns at five. Four demonstrations
preserve both teaching types after any holdout from five consecutive raw draws.
Four exact numeric controls set height, width, active columns, and distinct
nonzero colors. `palette_size` aliases the color count; `texture` is diagnostic.

The rule and validator accept lawful blank, singleton, full, and already-settled
grids. Final evidence includes 60 passing portable tests and an actual Racket
census of 300 lessons and 1,500 query rotations. The battery remains 10/12,
with two lawful-input heuristic failures. The retained bottom-row audit awaits
explicit maintainer resolution. See [current notes](notes.md) for evidence,
controls, and scope. Finite rival checks do not grant training admission.
