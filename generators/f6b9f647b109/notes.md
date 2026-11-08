# Working notes: f6b9f647b109

## 2026-09-29 review: factor-crossed lesson schedule

The prior four-slot schedule was semantically valid and passed the full battery, but its ordinary support coupled each direction to exactly one `(major_axis, distance_profile)` pair. Override coverage proved all combinations were constructible; it did not make those combinations part of the default training distribution. A direction-conditioned learner could therefore absorb the four scheduled templates instead of learning that phase order is invariant to direction, dominant axis, and distance regime.

Version 3.1.0 replaces that schedule with a sixteen-slot factor crossing. Every cyclic four-example lesson still contains all directions, both dominant axes, compact and extended cases, and at least two canonical-size anchors. Over one period, each direction appears with all four axis/distance pairs. The fifth/query slot repeats the first demonstration's direction but changes its axis/distance pair, making the recombination observable at lesson level. The Racket rule and `RULE_HASH` are unchanged.

`workspace/analyze_schedule.py` replays actual generated grids and verifies the support matrix, sliding-window guarantees, anchor floor, and query recombination. Run it directly or with `--json`.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `434c1e06b199edceb099b5b43e64d115737d700f39b3f7944324315957412fde`.

# Decisions for `f6b9f647b109`

All paths below are relative to `WORK/`. The selected Racket authority and `RULE_HASH=b267fa2de39d` remained unchanged.

## D1 — reject coercion at every public entry point

**Original choice/rationale.** `generate` delegated dimensions to `gen_ctx` helpers and used the identity values without a common strict boundary; `schedule_profile` reduced `sample_index` modulo the schedule period. This made valid calls convenient but allowed booleans, floats, numeric strings, negative indices, and invalid difficulty values to enter inconsistently. No current rationale for that coercion was documented.

**Alternatives considered.** Keep coercion; validate only `generate`; validate only dimensions; add one shared strict boundary used by both public entry points.

**Probe.** New contract tests were written first. Against the baseline, 52/66 failed (`checks/tdd-contract-red/result.json`). The packet defect lint independently reported 84 coercible-scalar findings in the before source.

**Decision.** Add `_validate_identity`, `_validate_difficulty`, and `_validate_call`; invoke them before schedule selection or RNG use. Require literal integers, a non-negative sample index, the four supported difficulty values, known override names, and literal `grid_h` / `grid_w` in `6..26`.

**Failure modes/limits.** Other declared string axes continue to rely on the existing `gen_ctx` exact-domain checks. The repair intentionally does not duplicate every helper validation.

## D2 — preserve valid behavior, version, and canonical authority

**Original choice/rationale.** The generator was already approved and its 16-slot factor-crossed schedule had passed the semantic, profile, override, and authority gates. The observed defect was an API-boundary issue, not an output-law defect.

**Alternatives considered.** Bump `VERSION`; edit the Racket rule; redesign the schedule; narrow valid override ranges.

**Probe.** The after battery, override matrix, profile floor, and selected task tests all ran on final generator SHA-256 `434c1e06b199edceb099b5b43e64d115737d700f39b3f7944324315957412fde`.

**Decision.** Keep `VERSION=3.1.0`, `RULE_HASH=b267fa2de39d`, all valid dimensions and categorical axes, and all generated outputs unchanged. Only invalid public calls change behavior.

**Failure modes/limits.** Downstream code that relied on undocumented coercion now receives an explicit exception. That is the intended contract correction.

## D3 — input distribution choices remain factor-crossed

| Choice | Current rationale | Alternatives checked | Retained limitation |
|---|---|---|---|
| `grid_h`, `grid_w`: `6..26` | Covers canonical sizes and broader lawful layouts while retaining room for a visible path. | Canonical-only sizes; smaller minimum; unrestricted dimensions. | Very large grids are intentionally excluded; exact canonical support is sampled rather than guaranteed on every draw. |
| `major_axis`: row/column | Ensures a visible straight middle segment and teaches both dominant-axis branches. | Balanced gaps; random unconditioned gaps. | Balanced gaps are absent, admitting Q1's conditional no-op shortcut outside production. |
| `distance_profile`: compact/extended | Crosses short and long paths with every direction and axis. | One continuous range; compact-only. | Within-class entropy differs; the named profile is a coarse category. |
| `direction`: four quadrants | Every four-demo window sees all directions, and the 16-slot period crosses each direction with all axis/distance pairs. | Random direction; old direction-correlated mapping. | Sample-index periodicity remains observable to callers that select only one residue class. |
| 16-slot deterministic schedule | Smallest exact full crossing of direction × axis × distance while preserving four-demo guarantees. | 4-slot, 8-slot, randomized blocks. | Determinism favors auditability over hiding schedule position. |
| 4 demos + 1 ordered query | Every production lesson retains the designed factor witnesses. | Arbitrary query rotations. | 21/1,500 arbitrary rotations were ambiguous; rotation is diagnostic only. |

Evidence: `checks/after/checks/f6b9f647b109_after_profile_floor.json`, `checks/after/checks/f6b9f647b109_after_override_results.json`, `checks/after/checks/f6b9f647b109_after_semantic_gate.json`, and `checks/lesson-census.summary.json`.

## D4 — propose phase position as the rule parameter

**Original choice/rationale.** The original family is defined by a path with one diagonal step, a contiguous straight block on the dominant axis, then the remaining diagonal steps. The assignment prioritized a nearby meaningful parameter without changing roles or replacing the reasoning structure.

**Alternatives considered.** Output-color reskin (cosmetic); endpoint-role reversal (changes task-defined symbols); diagonal direction/count mutations (risk unrelated path families); straight-block phase position.

**Probe.** Test-first prototype tests required exact canonical program preservation, one episode-level parameter choice, both settings, actual Racket execution, Python parity, and demonstration/query disagreement. The red run failed 2/68 because no prototype existed; an intermediate run exposed duplicate equivalent canonical rows; another exposed an incorrect Racket invocation shape. The final run passed 68/68.

**Decision.** Use `straight_block_position={after_first_diagonal,before_diagonals}` with canonical default `after_first_diagonal`. Preserve endpoints, colors, shortest Chebyshev connection, dominant-axis selection, and a contiguous straight block. Keep the prototype outside production.

**Failure modes/limits.** The retained seeds 0 and 1 are bounded evidence, not universal identifiability. The prototype has no production parametric API or approval.

## D5 — deduplicate equivalent canonical rows, reject conflicts

**Original choice/rationale.** The portable canonical ledger contains two rows for this content hash that carry the same program text. The first prototype incorrectly assumed exactly one row.

**Alternatives considered.** Select the first row silently; require one row; deduplicate identical programs but raise on different programs.

**Probe.** `checks/tdd-parametric-green/result.json` failed because two rows were found. Inspection showed their canonical programs were byte-equivalent.

**Decision.** The task-local prototype deduplicates identical program strings and raises if rows conflict. It does not choose silently among different authorities.

**Failure modes/limits.** This logic is local; F1 recommends a shared helper so future prototypes do not reimplement ledger semantics.

## D6 — keep ordered production despite rotation ambiguity

**Original choice/rationale.** The task's schedule is constructed around four consecutive demonstrations and a fifth query that recombines factors. Arbitrary holdout position was not the production contract.

**Alternatives considered.** Claim rotation support from the 60-case smoke; redesign the schedule until all rotations pass; retain ordered production and report rotations honestly.

**Probe.** The after semantic smoke found 60/60 diagnostic rotations unambiguous, but the larger 300-lesson census found 21/1,500 ambiguous rotations while all 300 production lessons passed.

**Decision.** Preserve the existing ordered assembly and report arbitrary rotations as unsupported. Do not make a broad schedule change for a non-production policy.

**Failure modes/limits.** A downstream system that shuffles pair roles must resample or add witnesses; this return does not certify that use.

## D7 — do not add balanced gaps to canonical generation

**Original choice/rationale.** The ordinary domain requires a strictly dominant axis so the straight middle segment is visible. Balanced gaps collapse the straight phase and reduce the intended sequence to diagonals only.

**Alternatives considered.** Add balanced gaps as shortcut counterexamples; reject them in `self_check`; retain them as validator-lawful but outside ordinary generation.

**Probe.** `checks/generator-shortcuts/balanced_gap_evidence.json` shows the rival fits 9/9 canonical demonstrations and 400/400 generated draws, while a lawful 6×6 balanced witness refutes it under Racket.

**Decision.** Keep balanced inputs validator-lawful but out of ordinary generation, and document the domain limitation. This avoids changing the original reasoning emphasis merely to defeat a rule outside the sampled family.

**Failure modes/limits.** The generator does not eliminate Q1's shortcut for solvers expected to generalize to all validator-lawful grids.

## D8 — audit targets are findings-only

**Original choice/rationale.** The assignment explicitly prohibits editing the two audit targets as part of the main repair.

**Alternatives considered.** Patch them opportunistically; report only source inspection; build source-bound reproducers.

**Decision.** Leave `15d6a8756e63` and `de83dfd70673` unchanged, retain runnable probes under `checks/audit/`, and report exact findings in `AUDIT.md`.

**Failure modes/limits.** These audits do not prove exhaustive defect sets and do not approve or reject future repairs.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-c238e83a9e70bf6d:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `023e6e5cdcad56b56c408f6de869573c635cd4c02802379b7f3f23d6114aad68`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Audited source is repo/generators/f6b9f647b109/generator.py, SHA256 023e6e5cdcad56b56c408f6de869573c635cd4c02802379b7f3f23d6114aad68. Explicitly resolve AUD-F6-S1 as superseded and fixed on current434c1e06b199edceb099b5b43e64d115737d700f39b3f7944324315957412fde. Original023e source accepted84invalid calls;newer accepted repair adds strict seed/index/difficulty/dimension boundaries. Four focused owner probes independently confirm bool seed,negative index,unknown difficulty andstring grid_h now reject before generation. This resolves only these scalar/override findings;separately documented21/1500rotation ambiguities and balanced-gap domain question remain unchanged. No fresh battery or semantic qualification. Quoted basenames refer to exact target-local paths: `checks/audit/f6b9f647b109-combined-command.log` `checks/audit/f6b9f647b109-combined.exit` `checks/audit/f6b9f647b109-combined/RUNTIME_MANIFEST.json` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_battery_summary.json` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_commands.jsonl` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_semantic_gate.json` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_semantic_gate.log` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_semantic_gate.ok` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_semantic_gate.receipt` `checks/audit/f6b9f647b109-combined/checks/f6b9f647b109_audit_summary.json` `checks/audit/f6b9f647b109-combined/checks/task_tests.xml` `checks/audit/f6b9f647b109-combined/progress.log` `checks/audit/f6b9f647b109-combined/result.json` `checks/audit/f6b9f647b109-defect-lint-command.log` `checks/audit/f6b9f647b109-defect-lint.exit` `checks/audit/f6b9f647b109-defect-lint/RUNTIME_MANIFEST.json` `checks/audit/f6b9f647b109-defect-lint/checks/f6b9f647b109_audit_battery_summary.json` `checks/audit/f6b9f647b109-defect-lint/checks/f6b9f647b109_audit_commands.jsonl` `checks/audit/f6b9f647b109-defect-lint/checks/f6b9f647b109_audit_defect_lint.log` `checks/audit/f6b9f647b109-defect-lint/checks/f6b9f647b109_audit_defect_lint.receipt` `checks/audit/f6b9f647b109-defect-lint/progress.log` `checks/audit/f6b9f647b109-defect-lint/result.json` `checks/audit/f6b9f647b109/strict-scalar-reproducer.json`

### Assessment or prior finding

## f6b9f647b109

### AUD-F6-S1 — Reproduced strict-scalar contract defect

Audited source SHA-256: `023e6e5cdcad56b56c408f6de869573c635cd4c02802379b7f3f23d6114aad68`.

The combined audit preset passed 13/13 portable tests and the strict semantic gate (`checks/audit/f6b9f647b109-combined/result.json`). A separate `defect_lint` failed with 84 `strict-scalar` warnings (`checks/audit/f6b9f647b109-defect-lint/result.json`). The minimal source-bound reproducer is `checks/audit/f6b9f647b109/strict-scalar-reproducer.json`.

That reproducer shows all four invalid probes were accepted and produced grids that passed `self_check`: boolean `seed=true`, negative `sample_index=-1`, invalid `difficulty="__invalid_difficulty__"`, and string override `grid_h="6"`. The resulting grid SHA-256 values are, respectively, `2b4f6938f88a1192f57b0dc8b2c05da3c13b8d1174eff619acc8ad4f76f5a39d`, `f56edeafa94b2338fb78aa55202d24e3dbe842f473b25e2fcb445bb5af15ce79`, `a78841a716c31d59c62139dc2beab970293915d724530a9997b44985664cfa39`, and `137c41552314f425bbe873333bbd00f176bfa7b6fcc6fc3a0d58cf19cb9bbb10`.

This is an actionable public-call/override validation defect, not a Racket-label disagreement. No source was changed and no approval is claimed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
