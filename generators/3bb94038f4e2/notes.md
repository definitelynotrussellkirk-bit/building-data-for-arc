# Working notes: 3bb94038f4e2

## 2026-10-04 review outcome

Final generator SHA-256: `4fa9f5f3c29b83ca61be1bbf46ae8b7ea31bee72f7363f9e5be70b36c663b776`.
Canonical Racket program was not edited; normalized rule hash remains `f19859825874`.

### Reproduced baseline defects

- Lint failed because `RULE_HASH` was absent.
- The module declared `grid_h=6..14` and `grid_w=7..16`, but band-specific `draw_int` calls rejected valid declared values. The 9,900-draw override matrix recorded 1,032 findings and also showed that unknown keys were silently accepted.
- Capped random placement could return a grid with no rule event; the baseline override probe reproduced default/self-check failures.
- No executable strict-profile, witness, rival, or lesson-identifiability contract existed.
- The 60-draw profile probe found only 8 exact canonical-profile hits, with zero support in both medium and hard.

Evidence: `checks/before/`, `checks/before-profile/`, `checks/before-semantic/`, and `checks/before-override/`.

### Final design

- Construct a lawful 6×7 semantic scaffold first, transform/place it inside the requested dimensions, then add isolated extra true gaps. The required event can no longer disappear through retry exhaustion.
- Alternate `core` and `broad` schedule profiles. Core draws heavily weight the three canonical input shapes `(7,7)`, `(6,8)`, and `(7,9)` with colors `{0,1}`. Broad draws preserve task boundaries with wide horizontal gaps, vertical gaps, `2,0,2`, and `1,2,1` near-misses.
- Keep the complete public dimension domain in every band; reject unknown keys and non-integer values; expose `observe_overrides`.
- Declare seven executable rivals, five semantic witnesses, two canonical-fitting shortcuts, and a lesson hook that fails only when a rival fits every demonstration and changes the query.
- Give each broad schedule slot a cycling isolated color signature. This is semantically inert but prevents production duplicate rejection from skipping the sole broad example in a three-demo rotation.

### Test-driven iterations retained

1. Missing `RULE_HASH` test failed, then the first constructive implementation passed the focused suite.
2. Official defect lint found generated maximum components too large relative to canonical morphology. A regression was added before reducing the scaffold's connected components.
3. A 300-lesson production census found 3 ambiguous held-out rotations out of 1,200 despite 0 ambiguous original lessons. Exact failures were easy lessons at `(seed,index pairs)` `(369778641,83/85)`, `(702232904,93/95)`, and `(2671966845,99/101)`: duplicate rejection skipped the second broad sample and left only core demonstrations. The targeted regression failed first; the broad signature repair then removed all 3 failures.

Evidence: `checks/tdd-red.log`, `checks/morphology-tdd-red.log`, `checks/lesson-census-final.json`, `checks/rotation-duplicate-tdd-red.log`, and corresponding green logs.

### Final evidence

- Official battery: 12/12 green under `checks/after3/`.
- Protected task tests: 62 passed under `checks/task-tests-final2/`.
- Direct focused tests: 61 passed, 1 expected skip because direct pytest lacked the protected Racket runtime; the protected run executed that parity test.
- Source-bound audit: 300 draws, 288 exhaustive cyclic rotations, 0 hook warnings, 0 ambiguous rotations, 138 canonical exact hits.
- Production sampler: 300/300 lessons, 1,200 pairs/rotations, 0 materialization errors, 0 ambiguities, 591 unique inputs.
- Final exposed solve: one revision, 3/3 visible demonstrations, earlier exposure `yes`, reference consulted `no`, bound to the final generator hash.

### Domain limits

The declared-rival checks are finite evidence, not a proof of universal identifiability. The alternating schedule and source-visible signature are intentional curriculum structure; future changes to lesson assembly or duplicate policy should rerun both the production rotated census and the task-local cyclic analyzer.
## Current reviewer considerations

Source SHA-256: `4fa9f5f3c29b83ca61be1bbf46ae8b7ea31bee72f7363f9e5be70b36c663b776`.

# Decisions — 3bb94038f4e2

## D1 — Keep the canonical Racket authority unchanged

**Decision.** Repair only the input generator and its tests/contracts. Pin `RULE_HASH = "f19859825874"`.

**Rationale.** Canonical train/test pairs, 120-input rule smoke, focused Python-oracle parity, protected real-Racket parity, and authority synchronization all agreed. The defect was that sampled inputs and lessons did not reliably expose the already-correct rule.

**Rejected alternative.** Rewriting or simplifying the Racket program would create an unnecessary authority change and obscure whether distribution repair alone fixed the task.

**Evidence.** `checks/before/checks/3bb94038f4e2_before_rule_smoke.json`, `checks/task-tests-final2/`, and `checks/after3/checks/3bb94038f4e2_after_authority_sync.log`.

## D2 — Replace capped retries with a constructive minimum-size scaffold

**Decision.** Place a lawful 6×7 pattern first, then embed it in any requested size and optionally add isolated true gaps.

**Rationale.** The baseline could exhaust placement attempts and return no `1,0,1` event; this violated both self-check and label value. Constructive placement makes the invariant true by design for every accepted dimension.

**Rejected alternatives.** Increasing the retry count still leaves a probabilistic failure and makes small override cases brittle. Post-generation rejection/resampling hides cost and can interact unpredictably with lesson duplicate policy.

**Probe.** `test_constructive_default_path_never_drops_the_required_gap` covers 160 draws for each of four difficulty settings; shared self-check and override gates add independent coverage.

## D3 — Separate canonical support from semantic breadth

**Decision.** Alternate `core` and `broad` profiles. Weight core dimensions heavily toward `(7,7)`, `(6,8)`, and `(7,9)` while retaining the full public size domain. Put all major near-misses in broad scenes.

**Rationale.** A single distribution that is always broad drifts from canonical morphology; a purely canonical distribution cannot refute canonical-fitting shortcuts. Alternation means every three consecutive examples include at least one broad counterexample while roughly half the draws can remain canonical-scale and binary.

**Rejected alternatives.** Narrowing the public dimension contract would break documented override support. Randomly sprinkling individual witnesses does not establish that each assembled lesson contains the needed combination.

**Evidence.** Final profile floor 31/60, semantic strict fraction 314/600, and production 300-lesson census.

## D4 — Make public dimensions exact, observable, and band-independent

**Decision.** Keep `grid_h=6..14` and `grid_w=7..16` legal in every band, reject unknown/non-integer controls, and expose `observe_overrides`.

**Rationale.** An advertised exact axis is a falsifiable API contract. Difficulty should change default weighting, not invalidate otherwise legal values unless incompatibility is explicitly declared.

**Rejected alternative.** Keeping band-specific ranges behind a global `AXES` declaration caused 1,020 generation errors in the baseline matrix and made typos look successful.

**Evidence.** `checks/before-override/` versus `checks/after3/checks/3bb94038f4e2_after_override.log`.

## D5 — Encode the task boundary as executable rivals and witnesses

**Decision.** Add seven pure rival functions, five witness predicates, two canonical-fitting shortcut claims, and `lesson_identifiable`.

**Rationale.** Comments about likely mistakes cannot be gated. Executable competitors let shared and task-local tools ask the training-relevant question: does a wrong rule fit every demonstration yet alter the query?

**Rejected alternative.** Checking only that the Racket output differs from the input catches identity but misses span, vertical, color-generalization, overwrite, and partial-fill shortcuts.

**Probe.** `workspace/reference_probe.py` independently extracts semantic features; `workspace/analyze_curriculum.py` reads the declarations from the selected generator.

## D6 — Preserve canonical component morphology after the first repair

**Decision.** Use separated small components in the core scaffold rather than long connected blue runs.

**Rationale.** The first constructive version passed functional checks but defect lint measured generated maximum foreground components around 4–5 versus canonical median 2. The rule does not require large components, so retaining small components improves distribution fidelity without reducing semantic coverage.

**Rejected alternative.** Waiving the lint as harmless would knowingly introduce an easily learned generator fingerprint.

**Evidence.** Failing `checks/after/` attempt, `checks/morphology-tdd-red.log`, and final green defect lint.

## D7 — Add a source-visible broad-slot signature after production duplicate failure

**Decision.** Set one isolated broad-template cell to colors `3..9`, cycling by broad slot.

**Rationale.** Production lesson assembly rejects duplicate inputs. Three exact lessons showed that duplicate broad slots could be skipped, leaving all-core demonstrations in a query rotation. A semantically inert signature keeps adjacent broad slots distinct without changing the Racket rule or the decisive near-misses.

**Rejected alternatives.** Random decorative noise would be harder to reproduce and reason about. Disabling duplicate rejection is a shared-policy change outside task scope. Forcing larger easy grids would reduce canonical/minimum-size support. Changing the alternating schedule alone would not protect against accepted-index advancement.

**Evidence.** `checks/lesson-census-final.json`, `checks/rotation-duplicate-tdd-red.log`, `checks/rotation-duplicate-tdd-green.log`, and `checks/lesson-census-final2.json`.

## D8 — Build reusable review tools instead of one-off assertions

**Decision.** Add `workspace/reference_probe.py` and `workspace/analyze_curriculum.py`, plus 62 protected tests.

**Rationale.** Future agents need an independent oracle, feature diagnostics, source/hash binding, canonical shortcut verification, and exhaustive cyclic rotations without reconstructing this review from prose.

**Limit.** The Python oracle is diagnostic, not authority. Real labels remain Racket-derived in protected tests and production census.

## D9 — Stop after final-source replay and finite rival coverage

**Decision.** Do not add more decorations, rivals, or axes after all required gates and both lesson analyses pass.

**Rationale.** Extra complexity would expand the fingerprint and failure surface without a reproduced defect. Current evidence covers official gates, exact controls, canonical support, actual production assembly, and every declared rival.

**Remaining uncertainty.** Undeclared model shortcuts remain possible; this is documented rather than overclaimed.
