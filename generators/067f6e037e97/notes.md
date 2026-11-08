# Working notes: 067f6e037e97

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-79f3a3e2ac11d5c3:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `403e6cc26c62b541b5c205d6fa133fad01f07793202a278e2810b791d4167ccd`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by current generator source SHA-256 4cd0627104c88d324a47d5062ec4e8930d12b8d7a5c538c1599d491e405582fa: ordinary generation now schedules a connected multi-cell texture within every three consecutive samples, so the one-stamp-per-object shortcut cannot fit the whole teaching window. Focused task tests pass, and the new parametric family separately proves per-cell behavior with protected Racket labels. This is a source repair disposition, not owner approval or training admission.

### Assessment or prior finding

## 067f6e037e97

**Reproduced teaching ambiguity — demonstrations support an object-level shortcut.** The intended rule paints the union of a clipped 3×3 neighborhood around every nonzero cell. A plausible rival paints one such neighborhood only around the row-major first cell of each 4-connected nonzero object. With seed 0, difficulty `medium`, sample indices 7, 8, and 9, every object is a singleton, so the rival exactly matches all three Racket-labelled demonstrations. Sample index 10 is a valid query containing component sizes `[1,1,1,4]`; the authority and rival differ at zero-based cells `(0,1)` and `(1,1)`, where authority outputs 8 and the rival outputs 0.

All four generated inputs pass the task's current `self_check`. Evidence: `checks/audit/067f6e037e97/evidence.json`, inputs in `checks/audit/067f6e037e97/input.json`, rival outputs in `checks/audit/067f6e037e97/rival_outputs.json`, and canonical Racket outputs in `checks/audit/067f6e037e97/racket.json`. The run is bound to generator SHA-256 `403e6cc26c62b541b5c205d6fa133fad01f07793202a278e2810b791d4167ccd` and rule hash `cfee16836461`. I did not modify this audit-only task.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-79f3a3e2ac11d5c3-v0001/audit_assets.json), manifest SHA-256 `c8f88d7a750f9ae75b18e74628f8eb4b950a56a24294ec123ce60974fac91ab3`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Reviewer-built native parametric family (2026-10-26)

The repaired base is paired with a task-local two-setting family under `workspace/parametric/`:

- `growth_scope=all_nonzero` is byte-identical to the canonical rule.
- `growth_scope=largest_object_color` first finds the unique largest same-color 4-connected object, then grows every input cell carrying that object's color by a clipped 3×3 Chebyshev neighborhood and paints the union color 8.

The constructive sampler supports 2–6 demonstrations and 1–4 queries. The two-demo qualification slice contains a unique largest size-6 object, a size-5 distractor, a remote singleton sharing the largest object's color, other-color distractors, and edge contacts. This makes the intermediate color input-dependent and makes the second step nonlocal. A protected-Racket counterfactual using the second-largest object's color changes the final output.

Source inventory: `workspace/parametric/evidence/manifest.json`. Reviewer authoring preflight: `checks/067f6e037e97/preflight/qualification.json`. Sequential witness: `checks/067f6e037e97/causal/witness.json`. Public one-query projection and first-turn checks are in `checks/067f6e037e97/preview-verify-final.json` and `checks/067f6e037e97/first-turn-final.json`.

Status is reviewer-reported source readiness only. Owner native qualification, acceptance, and training admission were not performed in this packet.
## Second-pass repairs (2026-10-26)

A combined-suite audit found that the old shared test-module name collided with the other assigned target, the blob branch could inflate explicit `seed_count=1`, blob cells did not always form a same-color object, and `full_grid` could choose color 8 and become an identity case. The suite now has a target-unique module name; blob overrides are exact while default blob lessons retain a same-color multi-cell component; and full-grid inputs use only non-8 colors. Current source is version 3.3.0, SHA-256 `4cd0627104c88d324a47d5062ec4e8930d12b8d7a5c538c1599d491e405582fa`. Fresh evidence is in `checks/067f6e037e97/` and the cross-family audit is `checks/parametric-family-audit-final.json`.
