# Working notes: 8d46d66e31b0

## 2026-10-24 review

- Reproduced invariant violation: seed 0/sample 2 selected color-2 cells `(1,1)`, `(1,3)`, `(2,2)`, three separate 4-connected components. The canonical rule extracts only the first component, while the previous `self_check` accepted the grid.
- Repair in version `1.2.1`: replace the disconnected template with a connected asymmetric L tetromino and make `self_check` require exactly one 4-connected color-2 component whenever a template is present.
- The documented `no_template`, `no_frames`, and single-cell-template degenerates remain valid. Tests cover the exact retained seed, an explicit disconnected impostor, all degenerates, and a 90-case cross-band generation sweep.
- Evidence: `WORK/checks/8d46d66e31b0-tests/result.json` after final verification. No parametric variant was added.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
