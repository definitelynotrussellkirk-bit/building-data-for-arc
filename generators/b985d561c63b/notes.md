# Current assignment: `review-529fa06ea6394047`

## Native parametric MAIN result

Production generator `generator.py` and canonical authority remain unchanged at SHA-256 `8a81e88ddb5d46c6eadd3fed5f2f283a532bde46e512ee1bc4d06ff3eec621a0` and canonical program SHA-256 `d28ede61a9c78ba345f33b47b9db17b0ea2334f382d7c6f17c8a1ec9cb6ef51a`.

The task-local native adapter now declares `stamp_anchor ∈ {top_left, hole_corner}`. `top_left` is byte-exact canonical behavior. For `hole_corner`, Step A locates the unique zero cell inside the colored source crop and classifies its corner; Step B aligns the complete crop, including zero, to that same corner of every larger gray target. The destination origin therefore cannot be chosen before the input-derived corner exists.

Native qualification passed for both settings at seeds 0 and 17 with three demonstrations and four queries per job (40 protected-Racket evaluations). The source-bound wrong-intermediate witness and independent reviewer replay both report `reviewer_replayed`. The finite teaching audit used the minimum supported two demonstrations and found no surviving declared fixed-corner or alternate-setting rival across the retained seeds. Public/private export checks passed for two four-query challenges. The complete staged task suite passed 322/322.

Primary evidence: `workspace/parametric/evidence/manifest.json`, `checks/b985d561c63b/qualification/qualification.json`, `checks/b985d561c63b/sequential-witness/witness.json`, and `checks/b985d561c63b/public-check.json` in the return packet layout.

Status is reviewer-ready only. Owner integration, fresh native qualification/acceptance replay, canonical approval, and any training admission remain pending. Evidence is finite over two settings, two qualification seeds, and the declared rival bank; it is not a universal identifiability or training-gain claim.

---

# Current notes: `b985d561c63b`

## Identity and authority

Current assignment: `review-c238e83a9e70bf6d`. Generator version remains `3.0.0`.
Final generator SHA-256: `8a81e88ddb5d46c6eadd3fed5f2f283a532bde46e512ee1bc4d06ff3eec621a0`.
Canonical rule hash: `c86839f15a5d`; canonical source SHA-256: `d28ede61a9c78ba345f33b47b9db17b0ea2334f382d7c6f17c8a1ec9cb6ef51a`.
No canonical Racket or canonical-data row changed.

The retained notes/workspace from prior assignment `review-19e0e8d6cd24f09c` were used only as a lead for the existing version-3 distribution and known rival vocabulary. All current claims below were remeasured against the pinned baseline/final bytes.

## Intended rule

Find the bounding box of all colored source cells (colors other than background 0 and target gray 5). Copy the entire bounding-box crop, including zero cells, to the top-left anchor of every original 4-connected gray target. Gray surplus outside the copied footprint remains gray.

The selected generator emits a canonical-style dense/congruent profile and an authority-supported punctured/surplus profile. Its default lesson policy is three demonstrations plus one query and declares four unique rivals: `nonzero_only`, `clear_all_gray`, `tile_target`, and `leftmost_source`.

## Current repair decision

The pinned baseline accepted booleans/floats/strings for `seed` or `sample_index` and negative `sample_index`. The public `generate` boundary now requires literal Python integers for both arguments and a nonnegative sample index. Validation occurs before schedule/RNG use. Negative literal integer seeds remain valid. The generator version and all lawful outputs are unchanged.

Focused evidence:

- `counterexamples/strict_call_scalars.json` is the minimal retained reproducer.
- `tests/test_call_contract.py` covers malformed calls and the retained fixture.
- RED: `checks/call-contract-red.log` (30 failed, 4 passed).
- GREEN/final: wrapper-backed task suite and portable receipt are 318/318.
- `checks/valid-call-equivalence.json`: 19/19 lawful calls byte-identical before/after.

## Final measurements

- Before battery: 11/12 green; only `defect_lint` failed.
- Final battery: 12/12 green; no advisory, failed, interrupted, stale or inconsistent stage.
- Lesson census: 300/300 lessons materialized (100 per band), 1,200 pairs and unique inputs, 0 production ambiguities, 0/1,200 query-rotation ambiguities.
- Exposed final-source solve: one attempt, 3/3 visible examples; masked correctness unknown.
- Blind-before-repair solve is retained separately and declares no earlier exposure/reference consultation.

## Proposed parametric extension

`workspace/parametric/prototype.py` is a separate **proposed/unapproved** episode tool. It selects one `stamp_anchor` value per episode:

- `top_left`: exact canonical default.
- `bottom_right`: same full crop aligned to the target's lower-right corner.

Two retained episodes cover both values with three demonstrations and one query each. All demonstrations refute the opposite anchor. Exact Racket/private and redacted public evidence is under `checks/parametric/stamp-anchor-v1/`. This prototype does not change the selected production generator or training approval.

## Known limits and open findings

The lesson census is finite and only tests declared rivals; it does not prove universal induction. The parametric evidence covers two retained seeds and a constrained dense-source/one-cell-surplus sampler. Visible-only solve results do not reveal masked-query correctness. Two unrelated audit generators have open strict-scalar findings; they were not patched in this assignment.

The strongest canonical-only shortcut is `nonzero_only`: all stored canonical source crops are dense. The selected generator already emits punctured separators; exact seed 0/index 0/medium evidence is in `checks/question-generator-shortcuts/counterexample.json`.
## Current reviewer considerations

Source SHA-256: `8a81e88ddb5d46c6eadd3fed5f2f283a532bde46e512ee1bc4d06ff3eec621a0`.

# Decisions for `b985d561c63b`

## D1 / B985-S1 — Reject implicit scalar coercion at the public boundary

**Input choice.** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0`. Keep negative integer seeds valid. Validate before schedule selection and before RNG state is created.

**Original rationale.** Unknown. The retained version-3 source validated difficulty and overrides but did not validate the two positional call scalars. The current task folder's retained notes/workspace from prior assignment `review-19e0e8d6cd24f09c` were used as a lead for the intended distribution and rule only; their claims were not treated as measurements of this pinned baseline.

**Evidence.** The completed baseline battery was 11/12 green and `defect_lint` reported 24 strict-scalar warnings. The focused RED run produced 30 failures and 4 valid-call passes (`checks/call-contract-red.log`). After the one-boundary validator, the same file was 34/34 green (`checks/call-contract-green.log`). A retained JSON fixture was then added under `counterexamples/strict_call_scalars.json` with an explicit RED→GREEN test. The final wrapped task suite and portable task-test stage are both 318/318 green.

**Alternatives rejected.** Coercing with `int(value)` would preserve the defect by accepting booleans, integral floats and numeric strings. Validating only in `GenCtx` would allow schedule logic to consume malformed `sample_index` first and would spread the contract across layers. Rejecting negative seeds would be an unrelated compatibility break; the packet's valid-call ledger includes a negative literal integer seed.

**Failure modes and limits.** This is a Python API contract, not a guarantee that callers in another language use the same scalar types. It intentionally does not constrain integer magnitude. Error classes/messages are tested, but downstream consumers should rely primarily on the exception type and named argument.

## D2 / B985-S1 — Prove valid draws did not move

**Input choice.** Capture 19 lawful calls spanning `None/easy/medium/hard`, multiple schedule positions, exact overrides, and a negative integer seed against the frozen baseline and final source.

**Rationale.** The repair sits before schedule/RNG construction, so byte equivalence is the strongest practical regression test for valid calls. `checks/valid-call-equivalence.json` records the exact generator hashes and each grid hash; all 19 match, and both aggregate digests are `32d50739a73fbd03c2a92c8b0c968c7998b1b53e753abe854ce18f54cbe785ee`.

**Alternatives rejected.** Comparing only `self_check` would miss deterministic output drift. Re-running random samples without preserving inputs/hashes would be difficult to audit. Nineteen calls are finite coverage, not proof over the unbounded seed space; the full battery and lesson census provide complementary coverage.

## D3 / B985-P1 — Prototype `stamp_anchor` as an episode-level parameter

**Input choice.** Add `stamp_anchor ∈ {top_left, bottom_right}`, selected once per complete episode. Preserve `top_left` as the byte-exact canonical default. The alternative aligns the same complete source crop, including zeros, to the lower-right of each gray target.

**Rationale.** This changes one relationship while preserving the original roles: identify the colored source bbox, find gray targets, and stamp the full crop. It is small, reversible, visible in demonstrations, and does not require a new object vocabulary. The generated inputs do not depend on the chosen parameter; a dense source plus one surplus row and column makes the anchors observationally distinct.

**Alternatives considered.** `copy_nonzero_only` was rejected as the parameter because it changes whether background is semantic and is already a known shortcut, not a clean positional variation. `clear_surplus_gray` was rejected because it couples stamping to target cleanup. Rotations/reflections were rejected because they add a second transformation concept rather than preserving the original copy relation.

**Probe.** Seeds 0 and 1 instantiate both settings in two deterministic episodes, each with three demonstrations and one masked query. All demonstrations refute the opposite setting, both query predictions disagree, 24 Racket applications are retained, and canonical replay checks six source pairs. See `checks/parametric/stamp-anchor-v1/report.json` and task-local tests.

**Failure modes and limits.** Evidence covers two values and two retained seeds, not all episodes. The sampler is intentionally constrained to dense sources and one-cell surplus. Declared-rival elimination is not universal identifiability. The prototype is separate, proposed and unapproved; it does not change production APIs or training admission.

## D4 / B985-Q1 — Treat `nonzero_only` as the strongest canonical shortcut

All stored canonical source bboxes are dense, so copying only nonzero cells is exactly equivalent on all six stored entries (three distinct inputs). A punctured final-generator input is the minimal semantic separator because intended full-bbox stamping writes source zeros over gray while the rival leaves gray untouched. The exact emitted witness is `seed=0`, `sample_index=0`, `difficulty=medium`; Racket execution and three differing cells are bound in `checks/question-generator-shortcuts/counterexample.json`.

This is not a remaining teaching failure in the sampled production policy: the 300-lesson census refuted all four declared rivals in every lesson and every held-out query rotation. It remains a useful canonical-only shortcut and therefore belongs in the question answer and future regression evidence.

## D5 — Preserve the canonical authority and version

No Racket source, canonical row, authority metadata, generator version, advertised axis or lawful distribution was changed. Rule smoke, authority sync and Racket lint are green in the final battery. Changing the version for a stricter malformed-call contract was considered unnecessary because no valid call or generated puzzle changed; maintainers may choose a policy-level version bump later.

## D6 — Audit findings are findings-only

The two drawn audit generators passed their combined task-test/semantic presets but failed an extra strict-scalar detector. I retained exact invalid calls, resulting grid hashes and empty self-check findings. I did not patch either target because the assignment explicitly makes audit repair optional and source edits are restricted to the selected task. The cost is two open, source-bound findings; the benefit is a minimal, reviewable selected-task delta.

## D7 — Evidence and solve policy

The initial and resumed battery attempts are both retained; interrupted/checkpointed work is not relabeled as a clean run. Direct pytest without the protected Racket environment is also retained as an environmental failure; only wrapper-backed runs support the green claim. Both solve lanes use visible-example feedback only, preserve exposure declarations, and make no masked-answer claim.
