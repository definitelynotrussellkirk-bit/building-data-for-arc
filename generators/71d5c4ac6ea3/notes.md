# Working notes: 71d5c4ac6ea3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/71d5c4ac6ea3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-26 native parametric build

- Preserved the selected canonical program byte-for-byte as setting `{"offset_mode":"as_drawn"}`.
- Added `{"offset_mode":"rotate_cw"}`: Stage A locates the color-9 anchor and extracts color-1 coordinates relative to it; Stage B rotates each relative offset clockwise and stamps color 8 around every color-2 seed on a blank output.
- Repaired the production generator's teaching and override contracts: every 2–6-demo lesson moves the anchor, all declared numerical axes are exact and recoverable, five inert controls were removed, incompatible texture/count overrides fail closed, and unknown overrides are rejected.
- The shared sampler uses matched inputs across settings, supports 2–6 demonstrations and 1–4 queries, and includes substantive 30x30 cases with at least seven offsets, five seeds, and broad occupied span. Fixed-origin, absolute-position, and reflection shortcuts are explicitly refuted.
- Focused evidence: `workspace/parametric/evidence/manifest.json` (reviewer-reported source inventory), including 17 task tests and `evidence/current/adversarial.json` with 32 episodes, 16 matched-input comparisons, eight 30x30 stress cases, shortcut/negative checks, and protected-Racket certificates.
- Protected authoring preflight: `WORK/checks/71d5c4ac6ea3/qualification/qualification.json` passed four jobs / 40 protected Racket evaluations. This remains `authoring_preflight_not_owner_qualification`; `owner_accepted=false`, `training_admitted=false`.
- Sequential witness: `WORK/checks/71d5c4ac6ea3/causal/witness.json`. Its counterfactual replaces the actual anchor with a fixed origin, changing the intermediate relative offsets and therefore the final stamped output under protected replay.
- Public projection: 16 one-query views verified; `WORK/checks/71d5c4ac6ea3/first-turn.json` passed 24 private-field invariance checks and four positive controls.
