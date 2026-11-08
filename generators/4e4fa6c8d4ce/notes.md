# Working notes: 4e4fa6c8d4ce

Review `review-9dff8738d2938418` replaced the 2.1.1 distribution after the
before battery found a missing rule hash, stale/dead axes, 20,809 override
findings, weak canonical-profile support, no semantic contract, and selected
Racket text drift.

Key decisions:

- Pin `RULE_HASH = adb72b5aa400` and synchronize both selected base authorities
  exactly to canonical `program_solution`; retain archival `raw_code` unchanged.
- Publish only six controls that are both honored and observable:
  `palette_size`, `block_size`, `layout`, `gap`, `palette_profile`, and
  `mask_profile`.
- Cycle through all four exact canonical `(height, width, color-count)` profiles
  in every difficulty band, while band-tagged keyed RNG varies mask, colors, and
  placement so bands are not byte-identical.
- Include a palette cell equal to the shape color at a filled mask position in
  two schedule slots. This is the missing witness against the strongest
  canonical shortcut: mask normally, but force shape-colored output cells to 0.
- Require connected/disconnected, 3×3/4×4, empty-mask, and asymmetric-mask
  witnesses through a semantic rival contract and every-three-demo lesson gate.
- Add focused tests plus `workspace/analyze_generator.py`, which independently
  executes the selected Racket rule and emits replayable shortcut/census JSON.

Verification evidence is under `checks/before`, `checks/after`, and
`checks/shortcut-witness-final.json`. The final after battery is 12/12 green.
## Current reviewer considerations

Source SHA-256: `13e8277e676c4b84e5d8c2bf27a4388b515227c0f93d06509c880ebeafc620b9`.

# Decisions — review-b03000a5ffc487ad

## Evidence basis

The immutable selected baseline was `cc7004707c4781c3da8b3888d102621e3fc601006208ca157239b00a825c7637`. The prior return `review-9dff8738d2938418` was used as a navigation lead because it explains the v3 distribution and retained shortcut witness; no prior pass claim was accepted without a fresh run. The final source is `13e8277e676c4b84e5d8c2bf27a4388b515227c0f93d06509c880ebeafc620b9`.

## D1 — choose a mask-polarity rule parameter

**Prior choice.** The selected generator had only one rule, with input controls for geometry, layout, palette profile, and mask connectivity. No episode-level rule parameter existed.

**New choice.** Prototype `mask_mode ∈ {filled, empty}`, chosen once per episode. `filled` is the canonical default; `empty` applies the same coordinate correspondence to absent rather than present shape blocks.

**Rationale.** This is the smallest parameter I found that changes the transformation while preserving the original reasoning pattern, object roles, spatial relation, and output shape. It is easy to instantiate as exact Racket, and every mixed-mask example distinguishes the settings.

**Alternatives considered.** Rotating/transposing the output would add a second geometric operation and weaken fidelity to the original family. Remapping palette colors would make color identity, not mask–palette correspondence, the central rule. Promoting `layout`, `gap`, block size, or palette size was rejected because those are input-distribution controls, not rule parameters.

**Probe.** `workspace/parametric/prototype.py` executes both Racket rules, an independent Python mirror, complete episodes, parameter rivals, and a shared-input disagreement. Evidence: `checks/parametric/mask-mode-evidence.json`.

**Failure modes and limits.** An all-filled or all-empty mask would make one variant degenerate, so the prototype declares mixed masks as an input constraint. Evidence covers two settings and one four-pair episode each, not all seeds. The prototype is proposed only; it does not alter catalog approval, training admission, or selected execution.

## D2 — require exact integers for declared integer axes

**Prior choice.** `palette_size`, `block_size`, and `gap` used coercing `draw_int`; the original rationale for accepting strings/floats/bools was not documented and conflicts with the published integer axis schema.

**New choice.** Use the shared `draw_int_strict` helper for all three axes.

**Rationale.** A control declaration should define an observable legal domain. Silent conversion made distinct invalid requests collapse onto legal values and was the root cause of the initial defect-lint failure.

**Alternatives considered.** Manual per-axis type checks would duplicate shared logic. Keeping coercion and documenting it would leave booleans and fractional values ambiguous. Changing the shared helper was outside the task-local patch boundary.

**Probe.** New parameterized tests first failed for floats and booleans, then passed after the minimal call-site change. `checks/request-contract/default-continuity.json` confirms 240/240 legal default calls are unchanged.

**Failure modes and limits.** This intentionally breaks callers that relied on undocumented coercion. Exact subclasses of `int` accepted by the shared helper remain governed by that helper's contract; call arguments themselves use exact `type(...) is int` to exclude booleans.

## D3 — validate seed, sample index, and difficulty at entry

**Prior choice.** The generator accepted booleans/floats/strings as seed-like values, negative or non-integer sample indices, and arbitrary difficulty labels. The original rationale is unknown.

**New choice.** Require exact integer `seed`; exact, nonnegative integer `sample_index`; and difficulty in `{None, easy, medium, hard}`. Apply validation in both `schedule_profile` and `generate`.

**Rationale.** After strict axis repair, the defect linter showed these were independent API-contract defects. Validation before scheduling avoids accidental Python indexing/modulo semantics and gives stable, explicit errors.

**Alternatives considered.** Validate only `generate` (rejected because `schedule_profile` is public and independently callable); coerce numeric values (same ambiguity as D2); or permit arbitrary difficulty salts (contradicts the declared three-band interface).

**Probe.** Retained TDD sequence: `checks/defect-lint/result.json`, `checks/defect-lint-2/result.json`, and clean `checks/defect-lint-3/result.json`. New regression tests cover each class.

**Failure modes and limits.** Legal output generation is unchanged. The accepted difficulty set is deliberately closed; a future new band must update the declaration and validation together.

## D4 — preserve the canonical authority and valid distribution

**Choice.** Do not alter the Racket rule, `RULE_HASH`, schedule, mask/palette logic, or legal axis domains.

**Rationale.** Fresh baseline evidence showed the semantic and distribution design was already strong. The concrete defect was at request validation, not the transformation. A rule or sampler rewrite would add risk without addressing the root cause.

**Probe.** Selected authority remains normalized hash `adb72b5aa400`; after battery authority sync and rule smoke pass. Direct baseline/final replay found 0 mismatches among 240 legal calls.

**Failure modes and limits.** The source file hash changes because validation code changed. The archival `raw_code` authorities remain intentionally text-divergent, as documented by the prior repair; selected authorities are synchronized.

## D5 — keep the parametric work outside production

**Choice.** Place the rule-family implementation under `workspace/parametric/` and tests under the selected task test directory, without adding a production axis or changing `generate`.

**Rationale.** The assignment asks for a runnable assessment but explicitly says the priority does not grant variant approval. Separation lets future agents replay and evaluate the idea without silently expanding the selected rule.

**Probe.** Public example files omit the hidden parameter and query labels; private evidence records the chosen setting and exact rule hashes. The canonical `filled.rkt` normalizes to the selected rule hash.

**Failure modes and limits.** The prototype currently reuses the fixed canonical input sampler; it does not test a joint sampler that intentionally balances parameter-specific teaching difficulty.

## D6 — lesson policy and evidence

**Choice.** Retain the production policy of 3 ordered demonstrations and 1 query, and require query-rotation identifiability in the large census.

**Rationale.** The selected generator already declares finite competitors and a three-demo teaching gate. The strongest canonical shortcut fits all 8 canonical pairs, so a larger source-bound census is warranted.

**Probe.** `checks/lesson-census.summary.json`: 300/300 lessons materialized, 1,200 pairs and unique inputs, 0 production ambiguity, and 0 ambiguity across all 1,200 one-query rotations. Every band contributes 100 lessons.

**Failure modes and limits.** This tests only declared rivals plus shared generic rivals and does not establish universal induction. Rotations reuse materialized bundles and do not enumerate every possible seed. The schedule period reported by the sampler is six; consecutive requested starts cover all residues repeatedly, but this was not the separate fixed-seed exhaustive-period mode.

## D7 — strongest shortcut witness

**Choice.** Retain `drop_shape_color` as the strongest plausible canonical shortcut and preserve its final-source witness.

**Rationale.** It fits 8/8 canonical pairs while making a simple, credible error: shape-colored palette values are zeroed. The selected schedule deliberately places such a value at a filled mask position.

**Probe.** `checks/shortcut-witness-final.json` is bound to final source `13e8277e676c4b84e5d8c2bf27a4388b515227c0f93d06509c880ebeafc620b9`, seed `8500`, sample index `2`, medium. Racket and Python mirror agree; shortcut differs at one cell. The witness appears in 40/80 local draws and each sampled lesson refutes the declared shortcut.

**Failure modes and limits.** This is strongest among the examined and declared plausible rivals, not a proof that no more compact shortcut exists.

## D8 — post-repair solve disclosure

**Choice.** Mark earlier rule exposure `yes`, reference consultation during solving `no`, and stop after the first implementation passed all 3 visible demonstrations.

**Rationale.** Generator repair necessarily exposed the rule before the fresh episode, so calling the later solve blind would be false. The implementation was nevertheless authored from the public challenge only during the solve phase.

**Limit.** The masked query answers are intentionally unavailable to the reviewer; the solve record establishes visible consistency, not hidden-query correctness.

## D9 — audit handling

**Choice.** Leave both audit targets unchanged. Record `928c39acebe3` as `No issue found` after bounded testing and record `7ae4da96dc92` as a reproduced canonical-domain/curriculum defect.

**Rationale.** The assignment separates adversarial audit from the selected task and explicitly requires no audit fixes. The second finding has exact Racket and rival outputs plus validator/domain status, making it suitable for a later dedicated repair.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7af9419bc1a75fd5:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `13e8277e676c4b84e5d8c2bf27a4388b515227c0f93d06509c880ebeafc620b9`. At disposition, audited bytes match the current source.

### Current decision

Audited source repo/generators/4e4fa6c8d4ce/generator.py SHA256 13e8277e676c4b84e5d8c2bf27a4388b515227c0f93d06509c880ebeafc620b9. Bounded no_issue:120deterministic inputs,111overlapping3demo windows,declared rivals only. Decisive direct Racket-enabled task run33/33; earlier interrupted wrapper is not a pass. No owner execution or peer source repair. Exact evidence: `checks/audit/.4e4fa6c8d4ce-task-tests.check.lock` `checks/audit/4e4fa6c8d4ce-task-tests.console.log` `checks/audit/4e4fa6c8d4ce-task-tests/checks/task_tests.xml` `checks/audit/4e4fa6c8d4ce-task-tests/progress.log` `checks/audit/4e4fa6c8d4ce-task-tests/result.json` `checks/audit/4e4fa6c8d4ce/probe.console.log` `checks/audit/4e4fa6c8d4ce/probe.json` `checks/audit/4e4fa6c8d4ce/probe.py` `checks/audit/4e4fa6c8d4ce/raw-pytest-with-racket.console.log` `checks/audit/4e4fa6c8d4ce/raw-pytest.console.log`

### Assessment or prior finding

## 4e4fa6c8d4ce

**Conclusion: No issue found** in the bounded declared-domain and declared-rival checks.

- Audited generator SHA-256: `13e8277e676c4b84e5d8c2bf27a4388b515227c0f93d06509c880ebeafc620b9`.
- Checked 120 deterministic generated inputs: 40 each for easy, medium, and hard. All passed the strict validator.
- Each of the four declared schedule profiles appeared exactly 10 times per band.
- Checked 111 overlapping 3-demo lesson windows. Every declared rival was refuted; all declared witnesses fired in their expected profiles.
- Protected-Racket-enabled task tests passed 33/33: `checks/audit/4e4fa6c8d4ce/raw-pytest-with-racket.console.log`.
- Reusable bounded probe and exact counts: `checks/audit/4e4fa6c8d4ce/probe.py` and `checks/audit/4e4fa6c8d4ce/probe.json` (probe SHA-256 `a9d440eaf4fd8444f5393dd47ac5e27e9b28c3de942c61e9dd6cef216b4ae522`).

**Scope limits.** The probe uses the generator’s Python rule mirror, with selected-Racket parity delegated to the 33 task tests. It covers 40 deterministic samples per band and declared rivals only; it does not prove absence of undeclared shortcuts. An earlier wrapper invocation printed the same 33 passes but was marked interrupted after the child; that retained artifact is not counted as the decisive pass.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
