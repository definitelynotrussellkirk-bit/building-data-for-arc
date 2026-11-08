# Current account: `bf9e0959b8ce`

## Intended rule

A full non-background row or column separates a sparse source region from an aligned key. For each source dot, compare its color with the adjacent aligned key value: a match routes to the source-side edge nearest the separator, a mismatch routes to the far outer edge, and the original source cell clears. Row and column forms are orientation variants of the same rule.

## Current selected generator

- Version: `2.2.0`
- Generator SHA-256: `626baeba976a6efa9c995f3e49f2927ad18d41193b9a5668b194008a7c6ce673`
- Pinned rule hash: `5fa488301c04`
- Lesson shape: 3 demonstrations + 1 query
- Schedule: six profiles with strict `row,col,row,col,row,col` orientation alternation; exact canonical anchors at profiles 0, 1, and 3.

## Review repairs

1. Public `seed`, `sample_index`, `difficulty`, and integer overrides now reject coercible/invalid scalar values instead of normalizing them.
2. The canonical-fitting `single_source_line` rival is declared. All six canonical pairs fit it, so generated inputs now guarantee at least two movement-axis source lines and thereby refute it.
3. The prior v2.1 schedule had 0/300 ambiguous production lessons but 99/1,200 ambiguous held-out rotations. Moving the third anchor from profile 2 to 3 and alternating orientations repaired this: final census is 0/300 production and 0/1,200 rotations ambiguous against declared rivals.
4. Selected solution `target_code` fields were synchronized to the exact executable canonical program. No Racket semantics changed; archival `raw_code` remains unchanged.

Exact retained shortcut witness: `counterexamples/single-source-line.json`. Focused regression tests: `tests/test_review_repairs.py`.

## Proposed parametric extension

`workspace/parametric/` contains a separate proposal for episode-level `route_near_when = match | mismatch`. `match` is the canonical default; `mismatch` swaps which comparison branch routes near while preserving all object roles and movement structure. Verification proves Python/Racket parity and distinguishes both settings for retained episodes. This is proposed only—not production-integrated or approved.

## Final evidence

- Battery: 12/12 stages green.
- Portable selected-task tests: 59/59 passed.
- Strict semantic draws: 600/600 accepted; canonical inputs 6/6.
- Profile floor: 31/60 exact, 47/60 envelope.
- Lesson census: 300 lessons, 1,200 unique pairs, 0 production ambiguity, 0/1,200 rotation ambiguity.

## Known limits / open findings

Finite declared-rival checks do not prove universal induction. The parametric proposal has only bounded two-setting evidence. General runtime/fixture issues discovered during review are recorded in `FEEDBACK_TO_CODEX.md`, not treated as task-local semantic defects.
## Current reviewer considerations

Source SHA-256: `626baeba976a6efa9c995f3e49f2927ad18d41193b9a5668b194008a7c6ce673`.

# Decisions for `bf9e0959b8ce`

## D1 — Preserve the selected rule and pinned hash

**Choice.** Keep the separator-keyed dot-routing semantics and `RULE_HASH = "5fa488301c04"` unchanged.

**Rationale.** The selected rule already matched all six canonical pairs, and the before `rule_smoke` and authority execution parity were green. The defects were in validation, shortcut coverage, lesson teaching, and authority text synchronization—not in the transformation.

**Rejected alternative.** Rewriting the Racket rule or changing its semantics would have expanded scope without evidence of a canonical error and risked invalidating existing authority bindings.

**Evidence / failure mode.** Final rule smoke and authority sync are green in `checks/after-v2.2/`. Any future semantic change should require a new declared rule hash and canonical review rather than being folded into this distribution repair.

## D2 — Reject coercion at every public scalar boundary

**Prior choice.** The baseline accepted booleans, floats, strings, negative indices, and unknown difficulty values in several paths; integer override axes could be silently coerced.

**New choice.** Require exact Python `int` for `seed` and `sample_index` (explicitly excluding `bool`), require nonnegative `sample_index`, allow only `None|easy|medium|hard` difficulty, and use strict integer override draws for `grid_h`, `grid_w`, and `n_dots`.

**Rationale.** The public schema says these controls are exact. Silent coercion makes reproductions and override audit results misleading.

**Alternatives rejected.** Normalizing strings/floats to integers was rejected because it hides caller defects. Removing the axes was rejected because the generator can honor them exactly.

**Evidence.** Baseline defect lint: `checks/before/checks/bf9e0959b8ce_before_defect_lint.log`. Final focused and portable tests: `checks/tdd/green-v2.2-task-local.log`, `checks/task-tests-v2.2/result.json`.

## D3 — Model the strongest canonical-fitting shortcut explicitly

**Choice.** Declare `single_source_line`: route only dots on the earliest densest source row/column and leave dots on other movement-axis lines untouched.

**Rationale.** Every usable canonical pair places all source dots on one movement-axis line, so this rival exactly fits all six labeled pairs while retaining a plausible object-level interpretation. Generic transforms and unconditional near/far rules were weaker because canonical labels already refute them.

**Generator change.** `_choose_source_positions` now guarantees at least two represented source-side rows/columns. The retained exact witness uses seed `8675309`, sample index `0`, difficulty `easy`, spans source rows `[2, 3, 8]`, and differs from the intended output in eight cells.

**Alternatives rejected.** Merely documenting the shortcut without changing the distribution would leave it unteachable. Requiring a fixed large number of source lines would unnecessarily narrow small-grid support; the minimal semantic requirement is at least two.

**Evidence and limits.** `repo/generators/bf9e0959b8ce/counterexamples/single-source-line.json` and `checks/after-v2.2/checks/bf9e0959b8ce_after_semantic_gate.json`. This establishes a finite counterexample, not universal uniqueness.

## D4 — Keep three demonstrations, repair the schedule instead

**Prior v2.1 choice.** Exact anchors were at profiles `0,1,2`, and lesson windows could contain three demonstrations of only one orientation after an arbitrary held-out rotation.

**Observed failure.** Production ordering had `0/300` ambiguous lessons, but the first 300-lesson census found `99/1,200` ambiguous rotations: `row_only` or `col_only` survived when the held-out pair removed the sole opposite-orientation example. The complete first witness is retained in `checks/lesson-census-v2.1-failure-extract.json`.

**New choice.** Move the third exact anchor from profile `2` to profile `3` and use the orientation cycle `(row, col, row, col, row, col)`. Every four consecutive pairs are now 2+2; holding out any one leaves both orientations among the three demonstrations.

**Rationale.** This repairs the teaching defect without increasing lesson size, changing canonical shapes, or changing the selected rule.

**Rejected alternatives.** Increasing `EXAMPLES_NEEDED` from 3 to 4 would raise data/inference cost and was unnecessary. Changing the third canonical anchor to row orientation would not preserve its canonical column role. Resampling only failed lessons would add hidden rejection complexity when a simple deterministic schedule invariant suffices.

**Evidence.** TDD red/green logs: `checks/tdd/red-rotation-behavior.log`, `checks/tdd/green-rotation.log`. Final census: `checks/lesson-census-v2.2.json` (`0/300` production and `0/1,200` rotations ambiguous).

## D5 — Synchronize authority text, preserve archival source

**Choice.** Apply the generated authority-sync proposal to the two selected solution records, changing only `/racket_target/target_code` to the exact canonical executable program.

**Rationale.** The baseline had execution parity but multiple exact-text groups, which made authority identity harder to audit. Exact synchronization removes that diagnostic divergence.

**Protection.** Both `/racket_target/raw_code` values remained unchanged. The canonical rule and declared rule hash were not modified.

**Rejected alternative.** Editing or deleting the archival raw snippets would destroy provenance without improving execution.

**Evidence.** `checks/authority-sync-proposal.json`, `checks/authority-sync-apply.log`, and final `authority_sync` in `checks/after-v2.2/`.

## D6 — Keep the parametric extension separate and episode-level

**Choice.** Prototype one parameter, `route_near_when = match | mismatch`, selected once per episode. `match` is the original default; `mismatch` reverses only which comparison result routes to the near edge.

**Rationale.** This is the smallest meaningful rule parameter that preserves the original object roles, aligned comparison, movement axis, and clearing operation. It creates genuinely different answers on the same inputs and is learnable because every demonstration contains both match and mismatch cases.

**Alternatives rejected.** Varying separator orientation is already an input parameter, not a rule parameter. Varying near/far destinations or source clearing would change more structural roles and create multiple simultaneous concepts. Per-pair rule selection was rejected because demonstrations would not teach one stable episode rule.

**Status / limits.** Proposed prototype only; not integrated into production or approved. Evidence is bounded to the two settings and retained seeds. See `repo/generators/bf9e0959b8ce/workspace/parametric/` and `checks/parametric/verification-v2.2.json`.

## D7 — Preserve stale solve provenance after source changes

**Choice.** Archive the completed v2.1 exposed solve under `checks/solve-stale-v2.1/`, including hashes, then prepare and finish a fresh solve from final v2.2 bytes.

**Rationale.** A solve is bound to its generator hash. Copying the old record forward would falsely imply it tested the final source; deleting it would lose real evidence.

**Evidence.** `checks/solve-stale-v2.1/README.md`, its `SHA256SUMS`, and final `solve/summary.json`.

## D8 — Evidence compaction without losing the failed witness

**Choice.** Omit the redundant 17.8 MiB full v2.1 300-lesson payload from the bounded return, while retaining its hash/size mapping, complete aggregate companion, and the full first ambiguous lesson with inputs, outputs, rivals, and source binding.

**Rationale.** The return has a 25 MiB expanded budget. The exact failure is reproducible from the retained recipe and witness; duplicating 299 additional failing-run lesson payloads would crowd out final proof.

**Evidence.** `checks/lesson-census-COMPACTION.md`, `checks/lesson-census.summary.json`, and `checks/lesson-census-v2.1-failure-extract.json`.

## Known limitations and open findings

- Declared-rival and bounded generic-rival checks do not prove that no other program fits the demonstrations.
- The parametric extension has not been catalog-reviewed, production-integrated, or tested across a broad seed census.
- The direct repository-root frozen fixture run has an environment-specific private-alias import failure; the supported portable selected-task test stage passes 59/59. This is reported as shared tooling feedback, not hidden as a generator failure.
- Audit-only defects in `c5a96370d612` and `40e128dec2ec` were reproduced but intentionally left unmodified; see `AUDIT.md`.

## 2026-10-24 native count-relay promotion (supersedes the earlier swap-only proposal)

The earlier `route_near_when = match | mismatch` prototype did not satisfy the required non-collapsing A→intermediate→B dependency and is no longer the active proposal. The native adapter now exposes `rule_mode = canonical | near_count_relay`, with exact canonical bytes as the default.

- **A:** execute canonical separator/key routing, producing near-edge and far-edge result sets.
- **Intermediate:** count routed dots on the near edge; construction guarantees a value in `{1,2,3}`.
- **B:** sort far-edge result dots by aligned coordinate, select the intermediate-th candidate, and relay it one cell inward.
- **Causal necessity:** on the retained 30×30 qualified query, the intermediate is 3 and selects far candidate `(29,6)`; forcing count 1 selects `(0,1)` and changes the protected-Racket output.

The family supports independent 2–6 demonstration and 1–4 query requests, four prefix-stable private queries, matched inputs between settings, canonical public-byte hashing, minimum-size cases, and a substantive 30×30 boundary query. Bounded self-review tested 1,520 named-rival lesson/query checks with no surviving demo-fitting, query-changing rival in that finite set. Native qualification covers two settings × two seeds with three demonstrations and four queries; the official causal witness is `reviewer_replayed`. Reviewer status is ready only: exact-source owner acceptance and training admission remain pending.

Current evidence:
- `workspace/parametric/evidence/current/audit.json`
- `workspace/parametric/evidence/manifest.json`
- `../../../checks/bf9e0959b8ce/qualification/qualification.json` in the return root
- `../../../checks/bf9e0959b8ce/causal/witness.json` in the return root
