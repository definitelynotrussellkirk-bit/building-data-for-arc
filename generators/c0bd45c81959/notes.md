# Working notes: c0bd45c81959

## review-d122508d0079b17e — 2026-10-25

- **Base defect and repair:** version 1.3.1 could reuse the same distractor color in a 3×2 block, producing a 3–3 nonzero tie even though the canonical rule assumes one unique mode. Version 1.3.2 samples distinct distractors, validates the fixed block geometry, and rejects every block without exactly one unique nonzero mode. The retained historical tie is now a regression test.
- **Canonical preservation:** `workspace/parametric/canonical.rkt` is byte-for-byte the catalog executable canonical program (`6477ed4263fd57cf26a5de62247d4c6cce5582deec55cb5f9bb74caf3df0ba8e`). No canonical authority or approval flag changed.
- **Native family:** default `all_modes` preserves the canonical 2×3 mode extraction in a zero border. `duplicate_bbox` first extracts the six modes, then finds the sole duplicated mode color and fills its macro-grid bounding box; Step B therefore consumes the input-dependent Step-A board.
- **Teaching/self-review:** deterministic 2–6-demo prefixes and four distinct queries use matched inputs across settings and deliberate top-left distractors. A 32-seed bounded audit covered 192 episodes, 1,472 visible pairs, 192 declared-rival certificates, 768 sequential public turns, and 65 protected-Racket evaluations with no failures.
- **Evidence status:** authoring preflight and protected causal replay passed on the exact source. Public projection/export/first-turn invariance passed. These are reviewer checks only; owner source review, native qualification/acceptance, and any training admission remain pending.
- **Next owner action:** apply the returned patch, verify the live source binding, run fresh native qualification and acceptance, then decide training admission separately.
