# Working notes: 3194379886a5

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 — review-82eef943d118bfcd

- Repaired generalized sampling so every non-public scene includes a pair of connected, non-dihedrally-equivalent shapes with the same row/column projection signature. This makes the intended D4 comparison necessary and directly defeats the retained projection-only shortcut.
- Preserved all exact public inputs and the canonical 4.0 rule; generator version is now 4.1.0 because generalized source bytes changed.
- Added the native `selection_rule` family: byte-exact `matched_prototype` and sequential `matched_color_pointer` (`match query → read matched panel color as pointer → select pointed panel`).
- The first two demonstrations deliberately use opposite pointer permutations so fixed-panel and cyclic-pointer rivals do not survive at the minimum supported demo count.
- Evidence: 17 focused tests plus 13 subtests; 32-seed bounded audit over 192 setting/count jobs and 1,472 pairs with zero declared-rival survivors; protected Racket authoring preflight for both settings at seeds 0 and 17; replayed wrong-intermediate witness; 16 public single-query views and 24 first-turn invariance checks.
- Lawful size limit is 6×27 because the grammar contains four equal square panels and three separators. Owner exact-source review, native qualification/acceptance, and training admission remain separate.
