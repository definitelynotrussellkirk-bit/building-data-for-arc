# Working notes: 0d191ce876ab

## 2026-10-26 source review and native parametric build

- Repaired the ordinary generator rather than trusting the old source: strict public axes now honor exact `grid_h`, `grid_w`, `n_keep`, and `n_drop`; unknown/coercive overrides are rejected; constructive footprints realize 1–6 exact survivors and include adjacent multi-core objects, removing the former one-centre-per-object shortcut.
- Preserved the canonical default byte-for-byte (`ddef27a306437674cef72f8caf84f0887cecbb4aabaa399b7c7a8a519058698c`).
- Added the native `preprocess` family: `identity` (canonical) and input-dependent `merge_1_into_2`, followed by the unchanged cardinal-neighbour survivor filter. Inputs are matched across settings, support 2–6 demonstrations and 1–4 queries, and include a substantive 30×30 fourth query.

## 2026-10-26 adversarial teaching round 2

- A 5,000-seed lesson search found two wrong merge-setting programs that could fit the original two demonstrations: merge then use any occupied neighbours (seed 9 gives a query disagreement), and correctly locate post-merge cores but paint every survivor colour 2.
- Replaced the weak remove-only lesson motif with an unaffected colour-6 core beside a mixed-colour occupied near-core. The same demos now force both same-colour neighbourhood semantics and preservation of unaffected survivor colours.
- The reusable lesson-stress tool checked seeds 0..4999: neither wrong rival fit all demonstrations; matched-input, setting-distinguishability, and duplicate-input checks had zero failures.
- Current source inventory: `workspace/parametric/evidence/manifest.json` (SHA-256 `176716310c358497c99b1e4a2f38734bc8b2f5ebfb37e97ccdd68118de9f2fc9`).
- Authoring preflight: `checks/0d191ce876ab-authoring-round2/qualification.json`; 4 episodes, 24 parametric pairs, 4 canonical base pairs, and 32 protected-Racket label evaluations.
- Bounded rival replay: `checks/0d191ce876ab-authoring-round2/bounded-self-review-v2.json`; 168 protected-Racket evaluations, with the actual program uniquely surviving every two-demo lesson.
- Sequential dependency witness: `checks/0d191ce876ab/causal-round2/witness.json`; the post-merge intermediate changes the neighbourhood values consumed by the survivor filter.
- Public projection/privacy: 16 single-query views verified; 24 private-field invariance mutations and 4 positive controls passed.

Limits: finite tests and named rival banks do not prove universal uniqueness. Owner exact-source review/acceptance and training admission were not performed.
