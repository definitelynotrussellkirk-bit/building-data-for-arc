# Working notes: 099aeda5aa7b

## 2026-10-26 source review and native parametric build

- Repaired the ordinary generator: strict exact `grid_h`, `grid_w`, `marks`, and `texture` controls; explicit incompatibilities for `on_axis`; deterministic nonzero-count preservation; and permanent color-conflict witnesses so generic fill cannot accidentally make a draw horizontally symmetric.
- The bounded minimum-grid stress exposed and fixed two concrete reliability holes (`plain`, seed 10, 2 marks; `on_axis`, seed 11, 3 marks). The final ordinary source passed 18,000/18,000 exact-axis cases across all four textures and mark boundaries 1/2/3/19/20 where legal.
- Preserved the canonical horizontal program byte-for-byte (`d623d8d2cccd6e562c0cb0ab0e18735d69496ebd85ef103f06181f466a78dca8`).
- Added the native `axis` family: horizontal (canonical) and vertical reflection, then nonzero overlay onto the original. Inputs are matched across settings, support 2–6 demonstrations and 1–4 queries, and include a substantive 30×30 fourth query.

## 2026-10-26 adversarial teaching round 2

- A multi-seed search found that reflection inside the occupied bounding box fit the original two demonstrations for most sampled episodes while disagreeing on later queries.
- The sampler now pins an occupied witness to the top and left and deliberately leaves bottom/right canvas margin, making full-canvas reflection observably different from occupied-bounds reflection in every lesson.
- The reusable lesson-stress tool checked seeds 0..4999: neither horizontal nor vertical occupied-bounds rival fit all demonstrations; matched-input, setting-distinguishability, and duplicate-input checks had zero failures.
- Current source inventory: `workspace/parametric/evidence/manifest.json` (SHA-256 `73e3e2ca513c4cabcfe2d278235df007262d03f0cb5f8e2c215f347f365bbfd8`).
- Authoring preflight: `checks/099aeda5aa7b-authoring-round2/qualification.json`; 4 episodes, 24 parametric pairs, 5 canonical base pairs, and 32 protected-Racket label evaluations.
- Bounded rival replay: `checks/099aeda5aa7b-authoring-round2/bounded-self-review-v2.json`; 216 protected-Racket evaluations, with the actual program uniquely surviving every two-demo lesson.
- Sequential dependency witness: `checks/099aeda5aa7b/causal-round2/witness.json`; overlay destinations and conflict colors depend on the selected-axis reflected intermediate.
- Public projection/privacy: 16 single-query views verified; 24 private-field invariance mutations and 4 positive controls passed.

Limits: finite tests and named rival banks do not prove universal uniqueness. Owner exact-source review/acceptance and training admission were not performed. The assignment's public-evaluation source task was used only as unverified inspiration; no relationship is claimed.
