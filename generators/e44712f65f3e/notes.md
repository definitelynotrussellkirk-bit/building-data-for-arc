# Working notes: e44712f65f3e

## 2026-10-26 repair and native parametric build

- Reproduced base defects: unused/degenerate axes were silently accepted, string/Boolean coercions passed typed overrides, and the self-check rejected the canonical two-frame input by requiring exactly one component.
- Repaired the base with a strict `frame_size`, `outer_color`, and `inner_color` contract; lawful size `3..8` across difficulty bands; and per-component validation of fully occupied square frames, uniform outer rings, distinct solid inner colors, disjointness, and expansion bounds. All canonical inputs pass.
- `placement=centered` remains the byte-exact canonical Racket program. `placement=nearest_edge` computes each frame's nearest canvas edge with tie order top, bottom, left, right and anchors the otherwise canonical expanded motif to that edge.

## 2026-10-26 second adversarial round

- Replaced fixed geometry with seed-varying lawful positions across all ten profiles. Four profiles contain multiple independent frames, all four nearest-edge directions occur, and dedicated profiles exercise top-left and bottom-right ties.
- The sampler backtracks to keep source objects disconnected and both centered and edge-anchored output boxes non-overlapping; the final profile remains a substantive `30 x 30` multi-object boundary case.
- Added package markers so ordinary combined pytest collection works with the historical shared test filename.
- Bounded evidence: 14 focused tests; 30 combined tests across both tasks; 500-seed Python fuzz; geometry variation in all 10 profiles, four multi-object inputs per full episode, four edge directions, and two tie frames; 200 protected-Racket profile evaluations for this task in the cross-task 400-evaluation fuzz.
- Exact-source authoring preflight passed with 4 jobs, 24 parametric labels, 4 canonical pairs, and 32 additional protected-Racket evaluations. The fresh centered-origin counterfactual changes the selected nearest-edge label and replays under protected Racket.
- Public evidence passed for 16 independently projected one-query views, including 24 first-turn private-field invariance checks and four positive controls.
- Remaining limit: this is reviewer-ready authoring evidence only. Owner source review, native qualification/acceptance, and any training admission remain separate; finite rivals and fuzzing do not prove universal identifiability.
- Next action: integrate these exact source hashes, rerun owner-native qualification, and review the nearest-edge-to-origin causal dependency before acceptance.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
