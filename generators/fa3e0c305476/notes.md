# Working notes: fa3e0c305476

## 2026-10-25 native parametric build

Built a two-setting native family under `workspace/parametric/`.

- `recolor_scope=all_objects` is the exact selected canonical Racket program, byte-for-byte.
- `recolor_scope=anchor_hole_matches` adds a sequential relay: count the holes in the row-major first cyan object, then recolor only objects with the same hole count using the canonical `{1→1, 2→2, 3→3, 4→7}` mapping.
- Inputs are matched across settings for the same seed/count request. The supported API is 2–6 demonstrations and 1–4 queries; qualification uses three demonstrations and four queries.
- The fourth query is a substantive 30×30 construction with cyan objects spread across all four boundaries.

The bounded teaching audit covers seeds 0 and 17 and all demonstration counts 2–6. It refutes eight declared rivals (`all_objects`, anchor-only, first-match-only, four fixed-count rules, and a second-object anchor), executes 12 labels in protected Racket, and records a wrong-intermediate causal case. This is finite evidence, not universal uniqueness.

Verification completed in this packet:

- 73 focused parametric tests passed before the portable legacy suite was included.
- The copied-runtime task suite passed 83 tests after replacing a brittle source-tree-relative import in the legacy test with `reviewer_support` binding.
- Native qualification passed all 2 settings × 2 seeds, with 40 protected-Racket evaluations.
- The causal witness was constructed and independently replayed from the native qualification receipt; substituting the second object's hole count changes the final grid.

Evidence:

- `workspace/parametric/evidence/current/audit.json`
- `workspace/parametric/evidence/manifest.json`
- packet checks at `WORK/checks/fa3e0c305476/qualification/` and `WORK/checks/fa3e0c305476/causal/`

No owner acceptance or training admission was performed.
