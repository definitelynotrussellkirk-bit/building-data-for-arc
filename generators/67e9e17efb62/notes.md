# Working notes: `67e9e17efb62`

## Intended rule

The input is a zero-background rectangle with one contiguous nonzero monochrome bar on row 0. The bar has length `L ∈ 3..8`, touches the left or right edge, and leaves at least one zero in that row. The output serializes same-color run lengths `1,2,…,L,L-1,…,2,1`, inserts one zero between adjacent runs, wraps row-major at the input width, and pads the last row with zeros. Input height and edge side are nuisance axes.

## Current canonical decisions

- `VERSION = 3.0.0`; `RULE_HASH = 824697c034e9`.
- Lawful generation distribution is unchanged from the selected baseline. One quarter of ordinary sample indices draw exact canonical profiles; the rest explore lawful dimensions and both edge sides.
- Public calls now reject non-literal scalar types, negative sample indices, invalid difficulty names, out-of-range enum/integer values, and unknown override keys before sampling.
- The semantic contract declares the full grammar, a `descending_tail` witness, and an `ascending_only` executable rival used by both semantic and lesson checks.
- Selected `racket_target.target_code` is exact canonical source; archival `raw_code` remains preserved. No Racket behavior changed.

## Evidence

- Baseline lead used: `counterexamples/review-6910db70eef2b3b1-v0001/retained/checks/audits/67e9e17efb62_unknown_override.json`; reverified against baseline source rather than trusted as current fact.
- Baseline battery: 8 green, 2 advisory, 2 failed (`checks/before/checks/67e9e17efb62_before_battery_summary.json`).
- Final battery: 12/12 green (`checks/final-battery/checks/67e9e17efb62_after_battery_summary.json`).
- Portable focused tests: 29/29 (`checks/task-tests/result.json`).
- Profile support: exact 12/60, envelope 44/60; exact per band 4/20 easy, 5/20 medium, 3/20 hard.
- Lesson census: 300/300 three-demo/one-query lessons and 1,200 rotations, zero ambiguity against the declared rival (`checks/lesson-census.summary.json`).
- Valid-call equivalence: 400 ordinary draws and eight override cases equal to baseline (`checks/final-equivalence/report.json`).

## Proposed parametric work

`workspace/parametric/` contains a separate proposed `peak_repetitions ∈ {1,2}` prototype. Value 1 is exact canonical behavior; value 2 repeats the peak-length run once. The setting is chosen once per episode. Both retained three-demo episodes refute the other setting and use actual Racket labels. This is not a production rule or approval change.

## Known limits / open findings

- The finite `ascending_only` rival does not prove universal lesson identifiability.
- The census does not enumerate every seed, all cyclic schedule starts, or undeclared programs.
- Empty/ragged grids and malformed public calls are rejected and are outside the lawful task domain.
- Archival `raw_code` intentionally differs in exact formatting from selected canonical source while retaining execution parity.
- No canonical blocker remains. Parametric integration requires a separate maintainer decision.
## Current reviewer considerations

Source SHA-256: `13448fabdbcd33fcaf640a2703ca099ea463aac1da11cbdbce569adae062f145`.

# Decisions for `67e9e17efb62`

## D1 — Preserve the canonical transformation and lawful sampling distribution

**Prior choice.** Version 3 samples one monochrome top-row edge bar and maps its length `L` to a serialized rise-and-fall sequence. One quarter of sample indices use exact canonical shape profiles; other draws expand lawful dimensions and edge side.

**Decision.** Keep that transformation, axis ranges, deterministic sampler, canonical-profile prior, and `VERSION = 3.0.0`. The review found API-contract and evidence defects, not a mislabeled transformation or weak lawful distribution.

**Evidence.** `checks/final-equivalence/report.json` compares 400 ordinary valid draws and eight explicit override cases between baseline and final source. Inputs and outputs are equal in every case; the ordinary set contains 337 exact unique grids. `checks/after/checks/67e9e17efb62_after_profile_floor.json` reports 12/60 exact profile hits and 44/60 envelope hits with nonzero exact support in every band.

**Rejected alternatives.** Broadening bar placement away from edges, adding multiple bars, or letting height affect the rule would alter object roles or compose a different task rather than repair this family. Raising the canonical prior was unnecessary because the existing floor already passes comfortably.

**Failure modes / limits.** Exact-grid uniqueness does not imply semantic diversity. The retained sampler still has a period-4 canonical-prior decision and finite axis ranges, which are intentional and visible in evidence.

## D2 — Make malformed requests fail before `GenCtx`

**Prior choice.** Values flowed into `GenCtx`, which accepted/coerced booleans, strings, floats, negative sample indices, invalid difficulties, and unknown override names.

**Decision.** Validate the public generation request at the top of `generate`: exact scalar types, legal ranges/enums, nonnegative sample index, and no undeclared keys. Keep cross-axis incompatibility checks explicit after dimensions are known.

**Reason.** Silent coercion and ignored typo keys create mislabeled experiments: callers believe they selected one axis value while the generator silently sampled another. Baseline defect lint measured 123 accepted invalid scalar probes, and the override checker accepted `__override_contract_unknown_axis__`.

**Alternative considered.** Coerce numeric strings/floats for convenience. Rejected because task-authoring calls should be replayable and exact; accepting `True` as color 1 or seed 1 is especially error-prone.

**Test.** `test_invalid_call_and_override_scalars_fail_loudly`; after-phase `defect_lint` and `override` both green.

## D3 — Defend the descending tail with one minimal executable rival

**Prior choice.** The generator had a Python mirror but no semantic witness/rival declarations, so the strict semantic gate could not evaluate teaching support.

**Decision.** Add a full-grammar strict hook plus `ascending_only`, a rival that omits the descending half. Bind it to a `descending_tail` witness and to lesson checking.

**Reason.** This is the smallest source-bound semantic obligation that separates the full canonical pattern from a plausible partial induction. It is independent of superficial dimensions and colors.

**Alternatives considered.** Width-dependent truncation, reversed runs, zero-separator omission, and direct lookup rivals are possible but were not added without evidence that they are competitive. Overpopulating a hand-written rival list can create maintenance noise and false confidence.

**Evidence.** The after semantic gate sees 600/600 strict lawful draws and refutes the rival. The 300-episode census refutes it in every production lesson and all 1,200 held-out-query rotations.

**Limit.** This declaration cannot catch undeclared shortcuts such as the `4f1ec6a61342` high-control threshold rival; that motivates `QUESTION_ANSWER.md` and feedback F1.

## D4 — Synchronize selected authority text, preserve archival source

**Prior choice.** Canonical `program_solution`, selected `target_code`, and archival `raw_code` were semantically equivalent but split across two exact source hashes. The selected `target_code` did not exactly match canonical.

**Decision.** Apply the authority-sync dry-run proposal only to selected `target_code`. Preserve `raw_code` byte-for-byte.

**Reason.** Selected execution authority should be exact and unambiguous, while archival source is provenance and need not be reformatted. The edit changes no Racket behavior or rule hash.

**Evidence.** `checks/after/checks/67e9e17efb62_after_authority_sync.json` reports `selected_synchronized_archival_divergent`; both exact source groups solve all 4 train + 2 test examples and execution parity is PASS.

## D5 — Use a one-parameter source-bound prototype, separate from production

**Parameter.** `peak_repetitions`, allowed values `{1,2}`, default `1`.

**Semantics.** Value 1 is canonical. Value 2 repeats only the maximum-length run once. The input constraints do not change; the episode must infer the hidden setting from demonstrations.

**Why this parameter.** It changes executed behavior at the core rise/peak/fall step while preserving every object role, spatial relationship, separator, wrapping operation, and output representation. It is a nearby family member rather than a cosmetic reskin.

**Alternatives rejected.** Output color would be mostly cosmetic; changing separator width would overemphasize serialization formatting; reversing the rise/fall order changes the directional reasoning more substantially; varying bar anchoring is already an input nuisance axis and does not change the rule.

**Episode policy.** Choose the parameter once from the deterministic episode seed; use the same value for all three demonstrations and one query. Reject any episode whose demonstrations do not refute the other setting. Public data hides parameters, source code, and query labels.

**Evidence.** `checks/parametric/peak-repetitions-v1/run.json` records exact programs, source hashes, seeds 0/1, both settings, three refuting demonstrations per episode, and a differing query. Racket—not only the Python mirror—labels every pair. All six prototype checks pass.

**Status.** **Proposed prototype.** It does not change `generate`, the selected rule hash, catalog approval, or training admission.

## D6 — Keep audit targets unchanged

The audit assignment asks for adversarial review, not repairs. `4f1ec6a61342` and `8114be8704cc` were checked against their assigned source hashes, and reproduction artifacts were retained under `checks/audit/`. No source under either audited generator was modified.

## Known limits and open decisions

1. Maintainers must decide whether to adopt the parametric runtime/API; this return supplies task-local evidence only.
2. The canonical lesson claim is finite and source-bound. Unknown rivals remain possible.
3. The two audit findings remain open in their respective generators.
4. A shared undeclared-rival search gate would provide more training-data value than adding more hand-written task-local rivals; see `QUESTION_ANSWER.md` and F1 in `FEEDBACK_TO_CODEX.md`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-6910db70eef2b3b1:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `aecce5f8a5c1a4b38b75d6efce433758b8ebf5886dda260a54f621d03fda23b0`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit static resolution of the old aecce5f8 unknown-key finding on already installed source 13448fabdbcd33fcaf640a2703ca099ea463aac1da11cbdbce569adae062f145. generate invokes _validate_generate_request before GenCtx; its unknown-key branch rejects bar_lenght and other undeclared keys. Current notes name this exact baseline lead and retain reported29 portable tests and12/12 final battery. Old finite-family observations remain bounded provenance; the new current-source left/right teaching finding stays unresolved. No owner execution or source edit.

### Assessment or prior finding

## 67e9e17efb62

Generator SHA-256:
`aecce5f8a5c1a4b38b75d6efce433758b8ebf5886dda260a54f621d03fda23b0`.
Selected rule SHA-256:
`1212a5180faaf8260ab3490d2b2cf153a607dd72076a17babe9a9e9b8637cb64`.
Normalized rule hash: `824697c034e9`.

**A2 — reproduced unknown-override defect.** At seed 2718, index 1,
`bar_len=3, bar_lenght=8`, the misspelled unknown key is silently accepted. The
result is exactly the valid baseline generated with `bar_len=3` alone and passes
the validator. This makes a caller's requested intervention unverifiable.
`checks/audits/67e9e17efb62_unknown_override.json` contains the exact input, observed
axes and real Racket output. Again the null rival output is intentional: this is
an API contract defect, not incorrect reference semantics.

**No semantic mismatch found in an exhaustive geometry basis.** All compatible
length/width combinations (`L=3..8`, width `5..23`, `L < width`) in both left/right
positions, fixed input height 3 and color 1, were generated and checked against
real Racket: 208/208 matched the independent row-major run-sequence model and
passed the validator. The 12 raw canonical pairs contain 6 unique pairs; all 6
unique pairs matched the independent model and Racket. Three deliberate malformed
inputs (a gap, a second bar color, and body noise) were rejected by the validator.
The audit used 215 Racket calls total; see `checks/audits/67e9e17efb62.json`.

**Domain limitation.** Under the documented single-bar grammar, input height and
left/right placement do not change the output. The tested basis has 104 distinct
structural outputs. Enumerating all nine nonzero recolorings in the independent
Python model yields 936 outputs. This color-expanded count is not 936 separately
executed Racket cases. It is evidence that the task's output family is small, not
proof that training is useless. It is better treated as a bounded curriculum
component than as an unlimited source of new structural reasoning. Suggested
repair: reject unknown override keys; no target source was modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-6910db70eef2b3b1-v0001/audit_assets.json), manifest SHA-256 `befce534bc9b87fc89347e5fc4b5fcf058fe005a0d37b52903651778baa3d6ac`.
<!-- arcpuzzles-current-audit-assessment:end -->
