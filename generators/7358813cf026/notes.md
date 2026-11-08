# Working notes: 7358813cf026

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7358813cf026/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-9ef69afea5bd0b81:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `78e2127b1eed53109573d2f798d7f3bb7c4d335c9d5fcd81bdf64cc032f5a989`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by current generator source SHA-256 1d0c57ca1ece72ed175a801d9e919dc1fcdfc1cdac6eead7dbeafcea2f8b1e3e: AXES now advertise the actual supported grid_h 8..11, grid_w 8..12, and singleton 3..5 domains; explicit endpoint overrides pass; unused axes were removed; palette_kind changes generated colors; and self_check now uses same-color 4-connected objects like the canonical Racket rule. Focused task tests pass. This is a source repair disposition, not owner approval or training admission.

### Assessment or prior finding

## 7358813cf026

Pinned source: `repo/generators/7358813cf026/generator.py`, SHA-256 `78e2127b1eed53109573d2f798d7f3bb7c4d335c9d5fcd81bdf64cc032f5a989`, rule hash `a01a7d7e0859`.

`AXES["grid_h"]` advertises integer values `4..20`, but the ordinary generation path narrows the draw to `[8,11]`. With seed `7991902016299830411` and sample index `2098244023`, `grid_h=8` is accepted, produces an 8×10 grid, and passes `self_check`; the same call with advertised-valid `grid_h=4` raises `ValueError: draw_int('grid_h'): override 4 outside [8, 11]`.

This is an API-boundary inconsistency: a consumer trusting the declared axis cannot exercise its advertised lower values. A maintainer should either make explicit overrides honor the full declared `4..20` domain in every applicable path, or narrow the advertised domain to the actual accepted range and test both boundaries. The bounded probe inspected one axis and one valid/invalid comparison only; no peer source was modified and no broader battery was run. The finding remains unverified pending maintainer assessment. Evidence: `checks/tickets/ticket-22fa45fbe13808da/result.json` and `checks/tickets/ticket-22fa45fbe13808da/command.log`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-9ef69afea5bd0b81-v0001/audit_assets.json), manifest SHA-256 `129e5cb4e9b46a84d92a4b6cb5b70c018161aaa71a9e7d0901a2fe12916151d1`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Reviewer-built native parametric family (2026-10-26)

The repaired base is paired with a task-local two-setting family under `workspace/parametric/`:

- `singleton_policy=erase_all` is byte-identical to the canonical rule.
- `singleton_policy=protect_largest_color` first finds the unique largest same-color 4-connected object, then preserves every multi-cell object plus each singleton whose color matches that largest object; all other singletons are erased.

The constructive sampler supports 2–6 demonstrations and 1–4 queries. The two-demo qualification slice contains a unique largest size-6 object, a size-5 distractor, both largest-color and distractor-color singleton noise, additional controls, and edge contacts. This forces the protected color to be derived from the input. A protected-Racket counterfactual using the second-largest object's color preserves a different remote singleton and changes the final output.

Source inventory: `workspace/parametric/evidence/manifest.json`. Reviewer authoring preflight: `checks/7358813cf026/preflight/qualification.json`. Sequential witness: `checks/7358813cf026/causal/witness.json`. Public one-query projection and first-turn checks are in `checks/7358813cf026/preview-verify-final.json` and `checks/7358813cf026/first-turn-final.json`.

Status is reviewer-reported source readiness only. Owner native qualification, acceptance, and training admission were not performed in this packet.
## Second-pass repairs (2026-10-26)

A combined-suite audit found that the old shared test-module name collided with the other assigned target and all three degenerate texture branches accepted but ignored explicit `grid_h`/`grid_w`. The suite now has a target-unique module name, and degenerate outputs honor every declared dimension endpoint. Current source is version 1.3.0, SHA-256 `1d0c57ca1ece72ed175a801d9e919dc1fcdfc1cdac6eead7dbeafcea2f8b1e3e`. Fresh evidence is in `checks/7358813cf026/` and the cross-family audit is `checks/parametric-family-audit-final.json`.
