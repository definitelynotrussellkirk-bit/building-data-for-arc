# Working notes: 2f4a0e633093

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 review decision

- **Base defects repaired:** `palette_kind` and `n_panel_cells` were dead controls and ordinary `self_check` allowed duplicate legends and malformed panels. Both controls are now live, request validation is strict, and the exact three-legend/three-monochrome-panel grammar is enforced.
- **Canonical default preserved:** `fixed_panels` returns the exact catalog Racket program byte-for-byte.
- **Native family added:** `area_ranked` discovers the three lower objects, crops binary masks, derives their increasing-area permutation, then uses that intermediate as the dynamic gallery row order.
- **Teaching self-review strengthened:** the first two visible demonstrations require different permutations, one separates occupied-cell area from bounding-box area, and dynamic scenes keep encounter order different from area order.
- **Current evidence:** 33 focused tests; 100 bounded seed/count jobs over 800 grids; constant-order and bounding-box-area rivals rejected in 100/100 jobs; source order rejected on 800/800 grids; protected-Racket authoring preflight; causal `wrong_order` witness; 16 verified one-query public projections; and shared first-turn privacy checks all passed.
- **Limit:** this is reviewer-ready source-bound evidence, not owner qualification, acceptance, universal uniqueness, or training admission. The next owner action is exact-source integration followed by fresh native qualification and acceptance.
