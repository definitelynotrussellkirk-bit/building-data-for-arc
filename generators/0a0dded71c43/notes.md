# Working notes: 0a0dded71c43

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 native parametric build

- Preserved the selected canonical program byte-for-byte as setting `{"mode":"fill_only"}`.
- Added `{"mode":"select_most_bridges"}`: Stage A performs the exact canonical 6-0-6 fill; Stage B computes completed 6/7 components, counts newly inserted bridge cells, and recolors the unique maximum component cyan. Component size is only a tie-break.
- The shared sampler uses matched inputs across settings, supports 2–6 demonstrations and 1–4 queries, and includes a substantive 30x30 fourth query. Winner location changes across examples, and a deliberately larger non-winner refutes the largest-component shortcut.
- Repaired the production generator's exact-axis contract: `n_gaps` is now recoverable from every returned grid, global override bounds match `AXES`, decorations cannot create hidden extra gaps, unknown overrides fail closed, and `no_gaps+n_gaps` is explicitly incompatible.
- Focused evidence: `workspace/parametric/evidence/manifest.json` (reviewer-reported source inventory), including 32 task tests and `evidence/current/adversarial.json` with 32 episodes, 16 matched-input comparisons, eight 30x30 stress cases, shortcut/negative checks, and protected-Racket certificates.
- Protected authoring preflight: `WORK/checks/0a0dded71c43/qualification/qualification.json` passed four jobs / 40 protected Racket evaluations. This remains `authoring_preflight_not_owner_qualification`; `owner_accepted=false`, `training_admitted=false`.
- Sequential witness: `WORK/checks/0a0dded71c43/causal/witness.json`. Its `skip_a` counterfactual substitutes the original input for the filled intermediate; Stage B then has no newly inserted bridges, producing a different final output under protected replay.
- Public projection: 16 one-query views verified; `WORK/checks/0a0dded71c43/first-turn.json` passed 24 private-field invariance checks and four positive controls.
