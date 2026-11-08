# Current account: 97bcb3b9194e

## Intended rule

On background `0`, find the separated filled rectangular components. Each has blue body cells (`1`) and one or more marks of any other nonzero color. Count **all** cells whose color is neither `0` nor `1`; exactly one rectangle has the minimum count. Return that rectangle's unchanged bounding-box crop. Canonical `RULE_HASH d21a7bae9946` is unchanged.

## Current generator decisions

- Version `4.1.1`; final reviewed SHA-256 `6e2d6a927f50fd4aa57a1c888cf28c819a01182a27616404495aeb128f3ba144`.
- Public scalars and exact axes reject booleans, floats, strings, negatives, out-of-range values, unknown keys, and the incompatible `winner_position=middle,n_boxes=2` pair.
- Six canonical `(height,width,distinct-color-count)` profiles are deterministic anchors every six samples; other samples retain band-aware variation.
- Marks use `canonical`, `four_only`, `six_only`, `two_three`, `five_seven`, or `eight_nine` palettes.
- The 12-step palette period is circular-window-safe: every four consecutive positions include at least two all-noncanonical palettes, so any one query rotation leaves a demonstration that refutes the `count_only_4_6` shortcut.
- Executable semantic hooks declare that shortcut as the current plausible rival and check lesson identifiability.

## Reversed prior choices

The inherited generator used only colors 4 and 6 and relied on permissive scalar handling. Those choices were reversed because the former made a wrong color-specific rule fit every canonical pair and the latter accepted invalid API requests. A first mixed-palette schedule was also reversed after the retained 300-lesson census found 3 production and 8 rotated ambiguities; the final period has 0/300 and 0/1,200 against the declared rival.

## Evidence

- Final strict battery: `checks/after-v2/checks/97bcb3b9194e_after_battery_summary.json` — 12/12 green.
- Final profile support: 17/60 exact, 38/60 envelope; all bands supported.
- Final semantic gate: 600/600 strict hits; noncanonical witness 383/600 across all bands; 60/60 checked rival claims hold.
- Final lesson census: `checks/lesson-census-v2.summary.json` — 300 lessons, 1,200 unique pairs, zero production/rotation ambiguities.
- Focused tests: 45 passing, including exhaustive four-sample circular windows.
- Exact pre-repair lesson witness: `counterexamples/review-5dbe0af1a8250935-v0001/lesson-ambiguity-before.json`.

## Authority and prototype

Two selected base-solution `target_code` fields were whitespace-resynchronized to canonical exact text; archival `raw_code` remains untouched and execution semantics did not change. A separate proposed `workspace/parametric/` prototype chooses `selection_mode={fewest,most}` once per episode and Racket-verifies both settings; it does not alter or approve production behavior.

## Known limits / open finding

Declared-rival checks are finite and do not prove unique induction against every possible program. The alternative `most` prototype may use stable row-major tie behavior for tied maxima. The inherited frozen root fixture remains nonportable and blocks the aggregate staged `task_tests` preflight; it is maintainer-owned and intentionally unchanged.

## Current owner source and evidence limits

Accept4.1.1 strict inputs,exact canonical anchors,all non-blue mark palettes and rotation-safe schedule refuting count_only_4_6. Canonical minimum-mark crop unchanged;selected text normalization statically verified. Reviewer reports12/12 battery,45 focused tests repeated fresh,300 lessons/1200 rotations/1200 unique inputs clean. Aggregate task tests remain BLOCKED before pytest by unchanged frozen fixture. Intermediate3/300 lesson and8/1200 rotation ambiguities retained. Proposed fewest/most4 episodes separate every demo/query;no production parameter API. Prior colors4/6 support audit resolved by this explicit palette/rival regression. Finite declared-rival scope;no fixture waiver. Owner checked hashes and public/private structure statically; tests and labels remain reviewer-reported.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4b72854d37690ed6:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3f478e0c7d134da408f8f70aaa2812b0102123b2d9626dfd87c3600a430d9d99`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolve exact colors4/6-only distribution finding. Accepted6e2d6a92 source generates all non-blue mark colors,declares count_only_4_6 and forces repeated separating lesson witnesses;45 focused regressions and300 lessons/1200 rotations report0ambiguity after retained failing intermediate. Canonical rule unchanged. Frozen aggregate fixture remains separately blocked;no owner rerun.

### Assessment or prior finding

## 97bcb3b9194e

**Reproduced shortcut / palette-coverage defect.** Generator v4.0.0, SHA-256
`3f478e0c7d134da408f8f70aaa2812b0102123b2d9626dfd87c3600a430d9d99`, emitted
mark colors only `{4,6}` in the checked domain even though the validator and rule
accept other non-blue mark colors. The rival “count only colors 4 and 6, then crop
the rectangle with the minimum count” matched all 12/12 canonical pair
appearances and all 600/600 production samples (200 per band; seeds
`800000..800199`, `810000..810199`, `820000..820199`, sample indices `0..199`).

A self-check-accepted 12×11 witness gives one box a single color-4 mark and the
other two color-2 marks. The intended rule counts all non-blue marks and selects
the first box; the rival ignores color 2 and selects the second. Selected Racket
execution is valid, matches the Python intended output, and differs from the rival.
Exact evidence: `checks/audit/97bcb3b9194e/finding.json`, `input.json`,
`rival.json`, `python-intended.json`, `racket.json`, and `racket-comparison.json`.

Reproduction from packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 97bcb3b9194e \
  --input ../checks/audit/97bcb3b9194e/input.json \
  --out ../checks/audit/97bcb3b9194e/racket.json
```

The witness belongs to the validator-accepted task domain but lies outside the
current production palette declaration. This is a finite canonical/600-sample
finding; the audit target source was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4b72854d37690ed6-v0001/audit_assets.json), manifest SHA-256 `e82ecbcecef6a1f1be6309377d941cdc8ae957eaf78e8d00d407fc2ec5a81ae8`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `6e2d6a927f50fd4aa57a1c888cf28c819a01182a27616404495aeb128f3ba144`.

# Decisions: 97bcb3b9194e

## D1 — Preserve the canonical transformation

**Choice.** Keep `RULE_HASH d21a7bae9946` and the rule “crop the unique rectangle with the fewest non-blue marks.”

**Original rationale.** The inherited implementation was already execution-equivalent to the canonical Racket and its geometric construction was lawful; the defects were API, distribution, teaching, and authority-copy issues rather than a wrong transform.

**Alternatives rejected.** Changing the target to a specific mark color, changing fewest to most in production, or rewriting object extraction would alter the task instead of repairing its evidence.

**Probe/limit.** Rule smoke, Racket lint, and authority execution parity pass. The separate `most` behavior is kept only in `workspace/parametric/` as a proposed prototype.

## D2 — Make public inputs exact rather than coercive

**Prior choice.** Validation was incomplete and context/scheduling helpers could coerce booleans, floats, or strings; the original rationale is unknown.

**New choice.** Require exact nonnegative `int` for `seed` and `sample_index`; exact `int` and declared ranges for integer axes; exact declared strings for enum axes; reject unknown overrides and incompatible `middle` with two boxes.

**Alternatives rejected.** `int(value)` coercion and accepting `bool` were rejected because they collapse distinct caller errors into reproducible-looking samples. Post-generation-only checking was rejected because it cannot prove the requested control was honored.

**Evidence/limits.** The independent defect lint and override gates pass. Validation covers the declared public API; internal helper arguments remain private.

## D3 — Add deterministic canonical-profile anchors without collapsing diversity

**Prior choice.** Dimensions were broad and plausible but produced 0/60 exact canonical `(height,width,color-count)` signatures. This likely favored free variation over measured support, but no rationale was recorded.

**New choice.** Every sixth sample uses one of the six canonical signatures: `(12,11,4)`, `(21,18,4)`, `(22,15,4)`, `(22,20,4)`, `(22,21,4)`, `(22,25,4)`. Other samples keep band-aware variation.

**Alternatives rejected.** Forcing every sample to canonical sizes would overfit six scenes; purely random hoping did not meet the floor; mutating the canonical corpus was unnecessary.

**Evidence/limits.** The final 60-draw profile gate measured 17 exact and 38 envelope hits with exact support in all bands. These are scheduled support points, not an estimate of a naturally random profile distribution.

## D4 — Generalize mark colors and make the lesson schedule rotation-safe

**Prior choice.** Production emitted only mark colors 4 and 6, matching the visible canonical palette. That made the simpler rule “count only 4/6 cells” observationally equivalent on all canonical examples and on too many generated lessons.

**New choice.** Use six palettes (`canonical`, `four_only`, `six_only`, `two_three`, `five_seven`, `eight_nine`) in a 12-step period where every circular four-position window has at least two all-noncanonical examples. On all-noncanonical samples, the fewest-mark winner is not placed first by accident; two-box scenes place it last.

**Alternatives rejected.** Independent random palette draws could still create all-canonical four-pair windows. One counterexample per four positions was insufficient under arbitrary query rotation because the sole counterexample could become the query. A fixed all-noncanonical palette would remove useful canonical visual support.

**Failure that changed the design.** The first repaired schedule passed the 12-lesson smoke but the 300-lesson census found 3 production and 8 rotated ambiguities. That failed iteration is retained in `checks/lesson-census.summary.json`; the exact easy-band witness is in the task counterexample directory.

**Evidence/limits.** The final regression exhausts circular starts for 72 samples per band; the final production census reports 0/300 and 0/1,200 rotations. This only refutes the declared `count_only_4_6` rival and generic gate mutations, not all possible hypotheses.

## D5 — Declare executable semantic contracts

**Choice.** Expose `strict_canonical_like`, `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` around the exact all-non-blue count distinction.

**Why.** A lawful label is not enough for training: demonstrations must reject plausible wrong rules. Executable rivals make this check repeatable and source-bound.

**Alternative rejected.** A prose note or a single handcrafted example cannot exercise production sampling or query rotations.

**Evidence/limits.** The semantic gate measured 383/600 witness firings across all bands and 60/60 checked witness claims with no violation. Rival declarations are finite and intentionally narrow.

## D6 — Synchronize selected authority text, preserve archival text

**Choice.** Replace only `target_code` in the two selected base-solution records with exact canonical text. Keep `raw_code` byte-for-byte as archival provenance.

**Why.** Baseline execution parity already passed, but the strict selected-authority gate requires exact text synchronization. Whitespace normalization alone was not sufficient for intake.

**Alternatives rejected.** Rewriting canonical `puzzles.jsonl`, changing program semantics, or normalizing archival `raw_code` would destroy provenance or expand scope.

**Evidence/limits.** `checks/authority-sync-proposal.json` records the proposed field-level edits; final authority sync reports selected synchronization and execution parity. The authority-set hash changes because selected copies changed formatting, not semantics.

## D7 — Keep the parametric variant bounded and separate

**Choice.** Add hidden episode parameter `selection_mode ∈ {fewest, most}` under `workspace/parametric/`; choose it once from the seed and use one setting for all three demonstrations and the query.

**Why suitable.** It changes one meaningful reasoning decision—the count extremum—while preserving segmentation, all-non-blue counting, stable ordering, and crop extraction. `fewest` is the exact canonical setting.

**Alternatives rejected.** Target-color, palette, size, or winner-position parameters only reskin inputs and do not change the executed transformation. Composing an unrelated spatial rule would leave the family.

**Evidence/limits.** Four Racket-labeled episodes cover both settings and distinguish them on every pair. The `most` extremum can tie and uses stable row-major behavior; this is disclosed rather than hidden. The prototype is proposed, not approved or wired into production.

## D8 — Use 3 demonstrations and test every query rotation

**Choice.** Retain the task's declared minimum of three demonstrations and assemble census lessons as four consecutive production samples: first three demonstrations, fourth query. Also hold out each of the four pairs in turn.

**Why.** Three demonstrations are the existing task contract. Query rotation tests whether identifiability depends on an accidental fixed order.

**Alternatives rejected.** Raising demonstration count would mask weak curriculum design and increase training cost. Testing only the production query missed eight ambiguous rotations in the failed schedule.

**Evidence/limits.** Final counts are 300 production lessons and 1,200 rotations. Downstream systems that never rotate queries still benefit; the stronger policy does not assert arbitrary reordering beyond these four pairs.

## D9 — Preserve the frozen-fixture blocker honestly

**Choice.** Do not edit `tests/test_generator_97bcb3b9194e.py`; add portable focused tests in new files instead and report completion as blocked.

**Why.** The assignment explicitly freezes the root fixture. Its fixed `parents[...]` data path fails before pytest in the staged runtime, independent of the repaired generator.

**Alternative rejected.** Patching or deleting the inherited fixture merely to turn the aggregate stage green would violate scope and hide a shared portability defect.

**Evidence/limit.** The focused suite passes 45 tests through the repository wrapper. The portable aggregate stage remains blocked until the maintainer migrates the frozen fixture to `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.
