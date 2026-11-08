# Current generator notes: `d2f8cb1c91b2`

## Intended rule

A 3×15 input contains four 3×3 panels separated by full color-5 columns. Infer the D4 transform mapping A to B, apply it to X, then merge transformed X with Y: zero yields to nonzero, equal nonzero values remain, and unequal nonzero values become 9. The selected Racket authority is unchanged and pinned by `RULE_HASH = a401bcfe7b0a`.

## Current public contract

- Version 3.0.0; `EXAMPLES_NEEDED = 3`; strict-canonical floor 1.0.
- Exact axes only: nonidentity `transform ∈ {r1,r2,r3,fh,fv,tr,atr}` and `palette_size ∈ {3,4}`.
- Every item is canonical 3×15 and contains x-only, y-only, matching-overlap, unequal-conflict, and both-zero branches.
- A/B uses a connected asymmetric support, so generated demonstrations identify exactly one D4 transform.
- Unknown axes, invalid axis values/types, and invalid difficulty names reject loudly.

## Reversed baseline decisions

The prior generator varied panel geometry, advertised dead texture/color controls, aliased `r3`, `tr`, and `atr`, and relied on random branch occurrence. Those choices were replaced with canonical fixed geometry, honest exact controls, independent D4 maps, and constructive branch guarantees because retained audits and red focused tests showed they produced invalid or weak training data.

## Curriculum and rivals

The twelve-step transform schedule places at least two `r3`/`atr` items in every four-item window. Therefore any one query rotation leaves a demonstration that refutes the retained transpose-alias shortcut. Each item independently refutes merge shortcuts through guaranteed branches. Declared lesson competitors are `transpose_aliases`, `no_transform`, `keep_y_on_conflict`, and `matching_is_conflict`.

Measured evidence: 12/12 production lessons and 48/48 required rotations identifiable in the semantic gate; 300 production lessons and 1,200 rotations with zero ambiguity/errors in `checks/lesson-census-final.json`.

## Validation and reusable probes

`workspace/reference_probe.py` independently implements D4 coordinates, split/infer/merge, branch and component statistics, observed-control extraction, semantic rivals, Racket parity, and distribution auditing. `tests/test_generator.py` contains 82 focused cases, including retained alias/conflict regressions and portable canonical/Racket checks.

## Known limits

- Fixed 3×15 geometry is intentional canonical fidelity, not geometric augmentation.
- Structural roles of colors 0, 5, and 9 are fixed; only data colors vary.
- The finite declared rivals do not prove identifiability against every hypothesis.
- Canonical A/B can be symmetry-ambiguous; the mirror uses deterministic first-match behavior to preserve canonical acceptance, while generated A/B is unique-transform.
- Any downstream lesson reordering outside the tested four-item windows must rerun lesson-level rival/rotation checks.

## Final evidence

Final generator SHA-256: `b36665d15b5049bd27de380915fdadab1378e44b747c2a8e20c081e099809cd3`. Official battery: 12/12 green in `checks/after/checks/d2f8cb1c91b2_after_battery_summary.json`. Override: 2,160/2,160 accepted, zero findings. Focused suite: 82/82 pass. No reference-rule change.
## Current reviewer considerations

Source SHA-256: `b36665d15b5049bd27de380915fdadab1378e44b747c2a8e20c081e099809cd3`.

# Decisions for `d2f8cb1c91b2`

## D1 — Keep the Racket authority unchanged

**Decision.** Preserve the selected rule and canonical rows; pin the existing rule with `RULE_HASH = "a401bcfe7b0a"`.

**Reason.** The defect was in the Python generator and its training contract, not in the selected Racket program. Racket rule smoke and authority execution parity pass after the repair.

**Rejected alternative.** Editing the rule or canonical examples to fit the baseline generator would hide the generator's transform aliases and domain drift rather than repair them.

**Evidence.** `checks/after/checks/d2f8cb1c91b2_after_rule_smoke.json` and `checks/after/checks/d2f8cb1c91b2_after_authority_sync.json`.

## D2 — Match the canonical four-panel 3×15 grammar exactly

**Decision.** Generate exactly four 3×3 panels separated by full color-5 columns at indices 3, 7, and 11.

**Reason.** Fixed geometry is part of the canonical composition, not an incidental texture. It keeps the learned problem focused on transform inference and merge semantics.

**Prior choice reversed.** Version 2.0.1 varied panel dimensions/counts and admitted shapes outside the canonical domain. That created distribution drift without a demonstrated rule-preserving benefit.

**Rejected alternative.** Continue varying panel size as augmentation. This would increase superficial diversity but train on a broader task than the authority specifies and complicate reliable transform uniqueness.

**Evidence.** Canonical pairs plus `strict_canonical_like`; distribution and diversity reports under `checks/after/checks/`.

## D3 — Use only honest, exact override axes

**Decision.** Publish two axes only: nonidentity D4 `transform` and `palette_size` 3 or 4. Reject unknown keys, invalid types, out-of-domain values, and invalid difficulty names.

**Reason.** Every advertised value is exactly observable in a generated sample and can be tested independently. A smaller truthful contract is more valuable than a broad dead control surface.

**Prior choice reversed.** The baseline advertised texture/color controls that were ignored, aliased, or incompatible with actual sampling.

**Rejected alternative.** Keep legacy axes for compatibility while silently ignoring them. This would continue contaminating controlled data generation and make audit failures nondiagnostic.

**Evidence.** 2,160/2,160 override draws with zero findings in `checks/after/checks/d2f8cb1c91b2_after_override_results.json`; focused exact-control tests.

## D4 — Generate asymmetric connected demonstrations

**Decision.** Choose connected 3×3 support shapes whose eight D4 images are all distinct, then paint A and its requested transform B with one data color.

**Reason.** A→B must identify a unique transform. Symmetric demonstrations allow multiple hypotheses before the merge rule is even considered.

**Rejected alternative.** Sample arbitrary support masks and retry only after an ambiguity is observed. Precomputing the small lawful candidate sets is deterministic, faster, and easier to audit.

**Evidence.** `_shape_candidates`, `_transform_matches`, strict validation, and `test_all_d4_transforms_match_independent_coordinates`.

## D5 — Guarantee every merge branch in each generated item

**Decision.** Construct X/Y so every item contains `x_only`, `y_only`, `matching_overlap`, `different_color_conflict`, and `both_zero` cells.

**Reason.** These are semantically distinct branches of the rule. Marginal random sampling previously omitted conflict examples and let a shortcut survive.

**Rejected alternative.** Raise random density and hope all branches appear often enough. That gives no lesson-level guarantee and can still omit rare branches exactly where they are needed.

**Evidence.** 600/600 witness hits for all branches in `checks/after/checks/d2f8cb1c91b2_after_semantic_gate.json`; branch tests in the task suite.

## D6 — Use three or four nonstructural data colors

**Decision.** Sample exactly three or four distinct colors from `{1,2,3,4,6,7,8}`, reserving 0 for empty, 5 for separators, and 9 for conflict output.

**Reason.** At least three data colors permit a same-color overlap and a different-color conflict without conflating structural roles. Four colors add lawful palette variety.

**Rejected alternative.** Permit 1–7 colors. One/two-color cases weaken conflict evidence; large palettes add little semantic value in only four 3×3 panels and drift from the canonical examples.

**Evidence.** Exact palette tests and override observations in `reference_probe.py`.

## D7 — Preserve canonical first-match behavior for ambiguous canonical A/B pairs

**Decision.** Generated examples are unique-transform, but the Python mirror selects the first exact transform in a fixed D4 order when validating canonical inputs with multiple matches.

**Reason.** One canonical pair is structurally ambiguous at the A→B stage; the selected Racket authority resolves it deterministically. The mirror must accept canonical data without pretending the ambiguity does not exist.

**Rejected alternative.** Reject all nonunique A/B pairs, which would incorrectly reject lawful canonical evidence.

**Evidence.** Canonical acceptance/Racket parity tests and semantic-gate canonical ambiguity report.

## D8 — Make complete lessons survive query rotation

**Decision.** Keep `EXAMPLES_NEEDED = 3` and use a twelve-item transform schedule in which every four consecutive items contain at least two `r3`/`atr` counterexamples. Declare four executable lesson competitors.

**Reason.** The historical implementation aliased `r3` and `atr` to transpose. With two such items in each four-item window, any one query rotation leaves at least one demonstration that refutes the alias, while per-item branch guarantees refute the merge rivals.

**Rejected alternative.** Independent random transform sampling. It has good marginal coverage but no guarantee that a particular three-demo lesson teaches the distinction needed by its query.

**Evidence.** 12/12 production lessons and 48/48 rotations in the semantic gate; 300 lessons and 1,200 rotations in `checks/lesson-census-final.json`; `test_every_four_item_schedule_window_survives_query_rotation`.

## D9 — Add an independent reusable probe rather than self-validating only

**Decision.** Add `workspace/reference_probe.py`, with independent transform coordinates and semantic analyses, and use it from focused tests.

**Reason.** A generator and test sharing the same buggy transform helper can agree while both are wrong. The probe gives future agents a compact, source-bound oracle and audit surface.

**Rejected alternative.** Assert only `self_check(generate(...))`. That catches malformed outputs but not correlated implementation errors.

**Evidence.** The historical alias test was red against the baseline and green after the repair; real Racket parity is also checked when the runtime is available.

## D10 — Treat fixed shape and finite rivals as explicit limits

The 3×15 shape is intentionally fixed because it is canonical; it should not be presented as broad geometric augmentation. The declared rival set is targeted to observed and plausible shortcuts, not exhaustive. A new dataset assembly policy, query order, or rival family must rerun lesson-level diagnostics rather than inheriting the current result by assumption.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d914c056785610b1:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ea25409ce9949fdc8c0ac94114b2c4d8b4d46aa431036ba2d279b1fe2758f1a5`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current source b36665d15b5049bd27de380915fdadab1378e44b747c2a8e20c081e099809cd3 has focused transform/palette repairs. Review-e3a7c38717c4e00e current-source probe covers all42 nonidentity-transform/two-palette/three-band combinations, observes exact requested values and every query conflict branch, plus144 declared-rival rotations. This bounded reviewer-reported recheck explicitly addresses old transform aliases, ignored palette and absent conflict branches; no owner rerun or universal proof. Old source ea25409ce9949fdc8c0ac94114b2c4d8b4d46aa431036ba2d279b1fe2758f1a5.

### Assessment or prior finding

## d2f8cb1c91b2

Version 2.0.1; generator SHA-256:
`ea25409ce9949fdc8c0ac94114b2c4d8b4d46aa431036ba2d279b1fe2758f1a5`.
Canonical normalized rule hash: `a401bcfe7b0a`.

**AD2-1 — Reproduced transform-control defect.** With seed 17, sample index 0,
easy difficulty, the three pins `transform="r3"`, `"tr"`, and `"atr"` produce
exactly the same complete input (hash
`d495272a96b1a55cdffc69c762a90cb7ea35e892c05264be1a1b725f931e6f0e`).
An independent D4 implementation finds the demonstration matches transpose
alone, not counterclockwise rotation or anti-diagonal reflection. The two helper
branches simplify algebraically to transpose. Therefore the uniqueness loop's
60 attempts cannot separate these aliases, but exhaustion is silently accepted.

The saved generated input and two counterfactuals differ only in the demonstration
output panel: one supplies a true counterclockwise rotation, the other a true
anti-diagonal reflection. All three pass the target validator and remain in the
intended four-panel geometric grammar; the generated `r3` case violates its exact
advertised transform. The public Racket outputs of both corrected inputs differ
from the original transpose output, proving the collapsed choices matter to the
query. These are not allegations that Racket mislabeled an input: Racket follows
the demonstrated transform correctly.

Evidence: `checks/audit/d2f8cb1c91b2/verified.json`, with full original and
counterfactual inputs, actual outputs, original-transpose rival outputs, source
hashes, and supported CLI replay command. The independent transform helper is
checked against a non-symmetric 1..9 matrix in the audit probe.

**AD2-2 — Reproduced ignored palette control.** At easy seed 23/index 0,
`palette_size=4` and `7` return identical inputs with seven visible colors
(including zero). Both are legal advertised values and the target validator
accepts the grid. The concrete seven-color grid, pins, observed count, and hash
are retained in `generated.json` under `ignored_palette_probe`. This is an exact
control failure, not a distribution-frequency claim. No random census or claim
about every ignored axis is needed for this witness.

**Domain questions, not established extra defects:** Source prose claims fixed
3×3 panels and guaranteed conflicts although normal generation varies panel
sizes and uses random query motifs. The audit did not perform a conflict-frequency
census, so it does not report an estimated rate. The preserved no-divider prose
also should be reconciled with width-based canonical splitting in a later repair.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d914c056785610b1-v0001/audit_assets.json), manifest SHA-256 `d8aa87ded89f5d1c377ba70b50a7a81bee53a544584dfad0b9aa35faefc91d2b`.
<!-- arcpuzzles-current-audit-assessment:end -->

## D11 — Episode-fixed conflict-policy prototype (2026-10-24)

**Decision.** Add a separate proposed family with `conflict_mode` in
`{marker, keep_x, keep_y}`. Every setting infers the demonstrated D4 transform,
applies it to X, and performs the same empty/matching merge; only unequal
nonzero overlaps differ. `marker` is byte-for-byte canonical, while the two
nearby variants preserve transformed X or Y.

**Teaching construction.** Reuse the reviewed source sampler, which guarantees
x-only, y-only, matching, unequal-conflict, and empty branches in every input.
Settings share identical inputs, each conflict changes all three labels, and
queries use a source-index range independent of demonstration count.

**Size decision.** Do not manufacture a 30×30 case. The canonical grammar is
exactly four 3×3 panels plus three full separator columns, hence 3×15. Enlarging
it would change panel inference rather than stress the same task.

**Evidence and disposition.** Protected Racket executed 42 labels across all
three settings and seeds 0/17; six public challenges passed the strict exporter
check; malformed settings, min/max counts, and a corrupted separator were
attacked. The native qualifier completed all six jobs and wrote a qualified
receipt. This remains a proposed, non-accepted family with
`training_admitted=false`; owner semantic review and explicit acceptance are
still required.
