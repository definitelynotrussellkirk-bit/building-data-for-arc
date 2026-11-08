# Working notes: aa45957d8241

## Current decision

Version 3.0.0 treats row 0 as an ordered selection legend, not a complete inventory. Canonical train pair 0 contains colour 8 outside the legend and train pair 2 contains colour 5 outside the legend, so the previous “no unreferenced body colours” invariant rejected lawful task inputs. `self_check` now permits up to two well-formed distractor components while still requiring exactly one 3–6-cell component for every selected colour.

The useful 2.1.0 repair was preserved: failed placement retries the entire layout, never a partial header/body state. The replacement controls are pixel-observable and exact. Default lessons cycle through selection, order, and combined witnesses; explicit controls take precedence over curriculum witnesses, so `n_distractors=0` remains feasible on every schedule residue.

Hard difficulty keeps its wide 10..18 × 14..24 branch but uses an exact canonical morphology on one third of un-overridden draws. This was added after the pinned profile census found zero hard-band exact hits. Seed and sample-index booleans, and negative sample indexes, are rejected before keyed generation.

## Evidence

Focused tests cover all four canonical inputs, the Python rule mirror, the canonical shortcut, every query rotation, exact-control boundaries, determinism, strict call arguments, schedule declaration, and pinned hard-band support. Native Racket smoke, strict semantic enumeration, canonical-profile floor, defect lint, and override-contract evidence are retained under `WORK/checks/`. The bounded adversarial probe found no issue across 288 exact-control corner draws and 1,080 rotated lessons against four declared rivals.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-fc199ba92f1bb6b0:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `4af826405865b7b6da9e4e78a09f304b9c6998c59b6964867c92bfb79c0e0654`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit owner disposition after accepted reviewer repair review-6c8d3b495a51b30d: current repo/generators/aa45957d8241/generator.py SHA256 338b4690fae09e6bdc89a528ed029a24a5873f702d56ba335e6547e783963dd6. Reviewer-reported evidence: 31focused tests,4/4canonical inputs accepted,120Racket parity cases, strict scalar/exact controls and executable selection/order lesson contract. Unlisted body colors are lawful distractors. No owner battery rerun, universal identifiability or training admission. The audit on 4af826405865b7b6da9e4e78a09f304b9c6998c59b6964867c92bfb79c0e0654 is resolved only for these repaired findings. Retained target-local evidence references: `checks/audit/aa45957d8241-combined/checks/aa45957d8241_audit_battery_summary.json` `checks/audit/aa45957d8241-combined/checks/aa45957d8241_audit_commands.jsonl` `checks/audit/aa45957d8241-combined/checks/aa45957d8241_audit_semantic_gate.json` `checks/audit/aa45957d8241-combined/checks/aa45957d8241_audit_semantic_gate.log` `checks/audit/aa45957d8241-combined/checks/aa45957d8241_audit_summary.json` `checks/audit/aa45957d8241-combined/result.json` `checks/audit/aa45957d8241-defect_lint/checks/aa45957d8241_audit_battery_summary.json` `checks/audit/aa45957d8241-defect_lint/checks/aa45957d8241_audit_commands.jsonl` `checks/audit/aa45957d8241-defect_lint/checks/aa45957d8241_audit_defect_lint.log` `checks/audit/aa45957d8241-defect_lint/result.json` `checks/audit/aa45957d8241-lint/checks/aa45957d8241_audit_battery_summary.json` `checks/audit/aa45957d8241-lint/checks/aa45957d8241_audit_commands.jsonl` `checks/audit/aa45957d8241-lint/checks/aa45957d8241_audit_lint.log` `checks/audit/aa45957d8241-lint/result.json` `checks/audit/aa45957d8241-selfcheck/checks/aa45957d8241_audit_battery_summary.json` `checks/audit/aa45957d8241-selfcheck/checks/aa45957d8241_audit_commands.jsonl` `checks/audit/aa45957d8241-selfcheck/checks/aa45957d8241_audit_selfcheck.log` `checks/audit/aa45957d8241-selfcheck/result.json` `checks/audit/aa45957d8241/audit_probe.py` `checks/audit/aa45957d8241/canonical-selfcheck.json`

### Assessment or prior finding

## aa45957d8241

**Classification: reproduced canonical-domain defect plus missing semantic contract; target left unchanged.** Audited generator SHA-256: `4af826405865b7b6da9e4e78a09f304b9c6998c59b6964867c92bfb79c0e0654`.

The task-local `self_check` rejects 2 of the 4 labeled canonical inputs:

- train pair 0: `body contains colors not referenced by row-0 codes: [8]`;
- train pair 2: `body contains colors not referenced by row-0 codes: [5]`.

Therefore the declared validator/domain does not contain the canonical task it is intended to model. The strict audit also finds no `strict_canonical_like`, `SEMANTIC_WITNESSES`, or `lesson_identifiable` contract, and there are no task-local or selected frozen tests. Separate lint evidence reports a missing `RULE_HASH`; defect lint flags 166 strict-scalar cases plus dead/overlapping texture behavior. Those additional findings reinforce the same conclusion, but the canonical self-check rejection is the smallest reproducible blocker.

Evidence:

- Compact canonical replay, including the two rejected inputs: `checks/audit/aa45957d8241/canonical-selfcheck.json`
- Strict combined audit: `checks/audit/aa45957d8241-combined/result.json`
- Semantic-gate log: `checks/audit/aa45957d8241-combined/checks/aa45957d8241_audit_semantic_gate.log`
- Self-check stage: `checks/audit/aa45957d8241-selfcheck/result.json`
- Lint stage: `checks/audit/aa45957d8241-lint/result.json`
- Defect-lint stage: `checks/audit/aa45957d8241-defect_lint/result.json`

Suggested owner action: first reconcile the header/body interpretation with every canonical pair and make `self_check` accept the canonical domain; then pin the rule, replace or remove nonobservable axes/degenerates, add portable tests, and declare executable semantic rivals/witnesses. No files under this audited generator were edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-fc199ba92f1bb6b0-v0001/audit_assets.json), manifest SHA-256 `ab710ea5497747279561c5ab7326092c1954ad2f9a916725cfbf49b3cd9d5092`.
<!-- arcpuzzles-current-audit-assessment:end -->
