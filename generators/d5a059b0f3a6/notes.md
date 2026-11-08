# Working notes: d5a059b0f3a6

## Current state

- Generator version: `3.1.0`.
- Final generator SHA-256: `8276303d89c43e360a4990344a3ccf04a0321e0b490aaa4300c36e3d0c86975d`.
- Canonical normalized rule hash: `77f0ca66f33e`; the selected Racket authority and canonical examples were not changed.
- Intended rule: find rectangles delimited by four disconnected, consistently oriented three-cell L corners; mirror each enclosed blue seed across the axis implied by its one-sided placement; delete blue distractors outside all frames.

## Prior lead and reproduced defect

The source-bound audit in return `review-f4cb9d0b248a69e5:v0001` (return ZIP SHA-256 `4f4354f3c90ddc1a8158dbbc56ef6a6fa10eeb4afc03827b43f3c6192fbd5249`, audited generator SHA-256 `98868b9812ca1ffbabafd8f96585dea2eee34145e12e6ff9d09eec52f96eb5d2`) was used as a lead. It retained seed 109, medium samples 0–2 with horizontal-only scenes and sample 3 with mixed axes: an always-horizontal rival fit all three demonstrations and disagreed on the query. The current review reproduced that shape before repair and retained the old evidence under `counterexamples/review-f4cb9d0b248a69e5-v0001/`.

## Decisions and repairs

1. **Preserve the rule; repair the curriculum.** The old probabilistic profile draw was replaced with a 16-slot cycle containing four public anchors and four each of horizontal, mixed, and vertical profiles. Every cyclic four-slot window has at least two mixed-axis scenes, so any one held-out query leaves a mixed-axis demonstration.
2. **Keep exact overrides truthful.** `_scheduled_choice` uses the full advertised domain and only moves the scheduled value into the RNG-selected position; an explicit `scene_profile` override still chooses the requested legal profile.
3. **Fail closed at the public boundary.** `seed` and `sample_index` must be exact integers, negative sample indices are rejected, `difficulty` is restricted to the supported enum, and unknown/non-string overrides are rejected before keyed RNG use.
4. **Make teaching claims executable.** The generator now declares `horizontal_only`, `vertical_only`, and `keep_distractors` rivals, mixed-axis and external-distractor witnesses, and a lesson hook that evaluates all three demonstrations against each labelled query.
5. **Make tests portable.** Task tests use `reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and `load_selected_generator` rather than fixed parent-depth paths.

## Verification

- Strict after battery: 12/12 green with required rotation identifiability; report `checks/after/checks/d5a059b0f3a6_after_battery_summary.json`.
- Portable task tests: 25 tests plus 18 subtests, all passing (43 JUnit cases); report `checks/task-tests-final/result.json`.
- Profile floor: 60/60 generated, 0 crashes, 10 exact-profile hits and 43 envelope hits; exact hits per band easy/medium/hard = 3/4/3.
- Exhaustive task-local schedule probe: 64 four-pair windows and 256 query rotations, 0 failures; report `checks/schedule/verification.json`.
- Production census: 300/300 lessons, 1,200 labelled pairs, 1,200 exact unique inputs, 0 production ambiguities and 0/1,200 ambiguous rotations against the declared rivals; compact report `checks/lesson-census-final.summary.json` and lossless full report `checks/lesson-census-final.json.xz`.
- Four-query episode: 3 demonstrations, 4 distinct labelled queries, all four query checks pass the lesson hook and declared rivals; report `checks/four-query.summary.json`.

## Proposed parametric extension

`workspace/parametric/` contains a separate, unapproved `mirror_mode` prototype. `single_axis` is byte-equivalent in normalized Racket rule hash to the canonical law; `both_axes` completes the full horizontal/vertical/180-degree orbit inside each frame. The verifier retained one episode per setting with 3 demonstrations and 4 queries, 7 shared distinct inputs, setting disagreement on all 7, and 14/14 Python–Racket label matches. This prototype is not integrated into production and does not change approval or training admission.

## Known limits and open findings

- The lesson evidence is finite and covers the three declared rivals plus generic mutation rivals; it is not a proof against every possible hypothesis.
- The default curriculum is deterministic by accepted sample index. Exact profile overrides can intentionally bypass its lesson-level balance, so custom lesson assemblers must supply their own teaching check.
- The production sampler and canonical rule remain limited to the existing frame grammar, seed geometry, palette roles, and distractor semantics; this review did not claim human-difficulty calibration outside that domain.
- No blocking finding remains for the selected repair. The `both_axes` parameter remains proposed only and needs owner review before any catalog/runtime integration.


## Current external prototype reconciliation

The source-bound pending finding in `evidence/parametric-external-followup-c26bd7b2af43b0b6/manifest.json` is preserved as provenance. The current prototype already had independent `n_train`/`n_test` controls, the 3-demonstration/4-query default, visible-content filenames, two setting-sensitive episodes, and exact Racket parity; those improvements were retained unchanged.

The narrow writer leak is repaired in `workspace/parametric/verify.py`: public challenges are now redacted and named as a complete plan, duplicate visible identifiers fail closed, and public files are emitted in lexicographic visible-filename order rather than private `ALLOWED_SETTINGS` order. A regression that reverses the private enumeration failed on the issued verifier and passes after the repair. Focused seed `20261023` verification executed both Racket programs on 7 shared inputs (14 exact Racket/Python checks), retained 3 demonstrations and 4 distinct queries per episode, and left generator SHA-256 `8276303d89c43e360a4990344a3ccf04a0321e0b490aaa4300c36e3d0c86975d` plus canonical rule hash `77f0ca66f33e` unchanged.

The bounded adversarial pass covered public/private export and verifier rejection paths: normal and reversed private enumeration produced the same sorted public names, while query-output leakage, hidden seed metadata, and visible-identifier collision were each rejected. Evidence is indexed by `workspace/parametric/evidence/conflict-reconciliation-review-f8f50425de4f205e/manifest.json`. The `both_axes` setting remains a finite, unapproved task-local proposal; this reconciliation is not catalog/runtime integration and does not prove absence of every possible side channel.

The writer-order leak is fixed, but exact public-byte conformance remains open: the saved public files use a16hex prefix of normalized visible JSON plus pretty-printed payloads. `workspace/parametric/evidence/public-export-conformance.json` records the two current files failing `public_id` and `canonical_bytes`. Use the shared serializer bytes and full64hex saved-byte ID before prototype promotion; canonical generator approval is unchanged.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f4cb9d0b248a69e5:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `98868b9812ca1ffbabafd8f96585dea2eee34145e12e6ff9d09eec52f96eb5d2`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

CurrentgeneratorSHA256 8276303d89c43e360a4990344a3ccf04a0321e0b490aaa4300c36e3d0c86975d explicitlyrepairs the retainedseed109 horizontal-only ambiguity with16slot mixed-axis curriculum. generators/d5a059b0f3a6/tests/test_generator_d5a059b0f3a6.py::test_default_windows_refute_forced_axis_rivals_under_query_rotation checksseed109 acrossall16starts/4bands/eachqueryholdout. Reviewerreported25tests+18subtests,64windows/256rotationszero failures,300lesson/1200rotationcensuszeroambiguities. Resolveonlythe priorhorizontal-onlyteachinggap on98868b9812ca1ffbabafd8f96585dea2eee34145e12e6ff9d09eec52f96eb5d2; no owner rerun or universalidentifiability claim.

### Assessment or prior finding

## d5a059b0f3a6

**Pinned generator SHA-256:**
`98868b9812ca1ffbabafd8f96585dea2eee34145e12e6ff9d09eec52f96eb5d2`.

### AUD-D5-1 — Reproduced teaching ambiguity: horizontal-only mirror

The intended task can contain horizontal and vertical frame axes. A plausible
wrong solver removes blue distractors outside frames, but always mirrors an
in-frame seed left-to-right. Seed 109 at difficulty `medium` produced profiles
`horizontal_frames`, `horizontal_frames`, `horizontal_frames`, then
`mixed_axes` for sample indices 0–3. Treating 0–2 as demonstrations and 3 as the
query, the rival matches all three exact Racket outputs and differs on the query
in six cells. All four inputs pass the target's `self_check`.

This is a concrete lesson-level ambiguity, not merely a suspected shortcut. The
Racket application recorded executed rule hash `77f0ca66f33e`, rule-text
SHA-256 `31e9d0247bca6af715f26388c3514b85fd851891dbbfbe74a477ec4b1f50e043`,
and the pinned generator hash. The catalog and executed hash fields should be
read from that receipt; I did not infer authority identity from source layout.

**Evidence:**

- `checks/audit/d5a059b0f3a6/horizontal-only-shortcut/metadata.json`
- `checks/audit/d5a059b0f3a6/horizontal-only-shortcut/input.json`
- `checks/audit/d5a059b0f3a6/horizontal-only-shortcut/racket.json`
- `checks/audit/d5a059b0f3a6/horizontal-only-shortcut/rival.json`

**Reproducer:** from the outer packet directory,
`python3 review.py run python3 -m arcpuzzles apply d5a059b0f3a6 --input ../checks/audit/d5a059b0f3a6/horizontal-only-shortcut/input.json --check-generator-domain --out ../checks/audit/d5a059b0f3a6/horizontal-only-shortcut/racket.json`.

**Suggested repair direction, not implemented:** balance each complete lesson so
its demonstrations include both horizontal and vertical axis behavior, declare
the horizontal-only rival, and check every permitted query rotation.

### AUD-D5-2 — Review infrastructure is not portable/complete

The source-bound combined audit preset failed. Its selected task test uses a
fixed `__file__/parents[...]` path and therefore fails portable preflight before
pytest; the semantic gate also reports no declared semantic contract. Evidence:
`checks/audit/d5a059b0f3a6-combined/result.json` and its audit summary. A broader
audit battery completed lint, self-check, and rule smoke green, then was
interrupted with nine stages still pending; it is retained as incomplete
rather than reported as a pass in
`checks/audit/d5a059b0f3a6-battery/`.

No target source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-f4cb9d0b248a69e5-v0001/audit_assets.json), manifest SHA-256 `c131ab3c1ede783014981472ff5e6868afe6b84876fcf5d7cea22f6a29f4bd39`.
<!-- arcpuzzles-current-audit-assessment:end -->
