# Working notes: 703a842c8e24

## 2026-10-02 review

### Baseline diagnosis

The imported generator's selected rule was correct, but its distribution and metadata were not:

- no rule-hash pin;
- most declared axes and all helpful textures were dead;
- headers were limited to 1..4;
- every body was a front-loaded short run;
- median generated object count was 1 versus canonical 4;
- canonical-profile support was 2/60 and absent in medium/hard;
- no semantic contract;
- 6,026 override findings and silently accepted unknown keys;
- `self_check` accepted structural impostors and malformed degenerates.

The canonical Racket rule was therefore preserved rather than edited.

### Selected design

Version 3.0.0 exposes only exact controls that can be observed: height 3..8, width 6..13, and two to six nonzero body colors. A diagnostic profile schedule cycles every four sample indices through canonical, wraparound, mixed-modulo, and dense-scattered cases.

The strongest canonical-ambiguous shortcut is “honor only headers 1..4; leave larger-header bodies unchanged.” Large-header profiles refute it. Three additional executable rivals test clipping, treating modulo zero as one, and using the first row's header globally.

Bodies keep the first post-header position zero, separating the connected header column from payload objects. Scheduled sparse/scattered/dense layouts restore canonical-like component counts without adding irrelevant noise.

### TDD and iterations

A new 11-test task suite was written and observed failing against the imported generator before implementation. It now passes completely. The first standalone lint preflight failed because `AXES['profile']['valid']` used `list(PROFILES)`, which made static metadata nonliteral; that evidence is retained under `checks/iterations/lint-attempt1/`. Replacing it with a literal tuple cleared the linter without changing generation.

### Final evidence

- full after battery: 12/12 green;
- canonical profile: 16/60 exact and envelope;
- semantic: strict 154/600, 4/4 witnesses, 4/4 rival claims, 12/12 lessons;
- rule smoke: 120/120 mirror parity;
- overrides: 19,800 accepted draws, zero findings;
- focused pytest: 11 passed.

### Known boundary

`profile` is diagnostic, not an exact semantic guarantee under arbitrary forced dimensions. For example, a 12-cell body cannot express a nonzero header equal to its width with ARC colors 0..9. Exact dimension/color overrides remain lawful; default scheduled profiles retain their promised witnesses.
## Current reviewer considerations

Source SHA-256: `6d7d32c5e2aaa3179d21ec687ed8721e10fea3f49945b573593a66b1aa50be40`.

# Decisions for 703a842c8e24

## 1. Preserve the canonical authority

**Choice.** Leave the Racket rule and canonical row unchanged; add `RULE_HASH = "3ecc6b0e255e"` and a Python diagnostic mirror.

**Original rationale.** The imported notes did not document a design rationale. The before rule-smoke stage was already green, so there was no evidence of an authority defect.

**Alternatives considered.** Rewrite or simplify the Racket rule; change canonical examples.

**Probe.** Canonical examples were replayed through the Python mirror, and the final rule-smoke stage checked 120 generated cases against Racket.

**Failure mode guarded.** A generator repair must not silently redefine the task. Final mirror parity was 120/120.

## 2. Replace dead metadata with three exact axes

**Choice.** Keep only `grid_h`, `grid_w`, and `n_body_colors` as exact public controls. Mark the internal curriculum `profile` diagnostic.

**Original rationale.** Unknown. The old implementation declared palette, position, color-count, shift-distribution, texture, and body-length controls but hard-coded or ignored most of them.

**Alternatives considered.** Implement all legacy axes; retain aliases but mark them diagnostic; delete override support entirely.

**Probe.** The baseline override checker reported 6,026 findings and 41,130 legacy multi-axis rejections. The replacement passed 19,800 draws and 220 cases with exact observer equality.

**Failure mode guarded.** Avoid metadata that appears configurable but is inert, and avoid difficulty-local bounds rejecting globally declared boundaries.

## 3. Use a deterministic four-example schedule

**Choice.** Select profile by `sample_index mod 4` so every consecutive four examples contain all semantic branches.

**Original rationale.** The old generator sampled one narrow family independently; it supplied no lesson-level guarantee.

**Alternatives considered.** Independent random profiles; weighted random profiles; one profile per difficulty.

**Probe.** Sliding windows starting at offsets 0 through 7 were tested. The semantic gate observed all profiles in all bands and found 12/12 lessons identifiable.

**Failure mode guarded.** Randomly drawing four examples can omit a low-probability counterexample and teach a shortcut even when the pooled distribution looks adequate.

## 4. Reserve one quarter of ordinary draws for the canonical manifold

**Choice.** The `canonical` profile emits exact 4x9 grids with headers 1,2,3,4 and a total palette of five to seven colors in every difficulty band.

**Original rationale.** The prior dimension ranges accidentally produced only 2/60 profile matches and none in medium or hard.

**Alternatives considered.** Broaden every profile until it sometimes matches; add a rare 5% canonical branch; make only easy canonical-like.

**Probe.** The strict profile floor measured 16/60 exact and envelope support, with at least one hit in every band.

**Failure mode guarded.** A semantically correct generator can still drift so far morphologically that it no longer trains on the public task's regime.

## 5. Teach large headers and modulo explicitly

**Choice.** The wraparound and mixed-modulo profiles use headers above four; mixed-modulo includes a row whose header equals its body width when representable.

**Original rationale.** The old generator restricted every header to 1..4, exactly the range used by the canonical demonstrations.

**Alternatives considered.** Keep 1..4 only; merely enlarge dimensions; rely on random large headers without a scheduled witness.

**Probe.** The declared `headers_1_to_4_else_identity` shortcut fits every canonical pair but is refuted by generated large-header witnesses. The semantic gate verified 60/60 checked disagreement cases.

**Failure mode guarded.** A learner could memorize four header cases rather than infer modulo arithmetic.

## 6. Force genuine cyclic wraparound

**Choice.** A wraparound row has a positive effective shift and a nonzero cell in the trailing wrap zone. The selected large header is coprime to body width when possible.

**Original rationale.** The previous bodies were short runs at the front, so some examples did not visibly distinguish rotation from a noncyclic move.

**Alternatives considered.** Random placement only; compare outputs after generation and retry; permit clipping-like examples.

**Probe.** `cyclic_wraparound_counterexample` compares the canonical transform with an executable clipping rival. The claim held on every checked witness.

**Failure mode guarded.** “Shift right and discard overflow” can resemble rotation when the wrap zone contains only zeros.

## 7. Break the single-object/front-loaded shortcut

**Choice.** Keep column 1 blank, create separated runs, and include a dense-scattered profile. Every row remains nonempty and has background.

**Original rationale.** The baseline generated one connected foreground object while canonical median object count was four.

**Alternatives considered.** Add arbitrary noise; rely only on color changes; copy canonical contiguous layouts exactly.

**Probe.** The task test requires at least two components in 90% of a 120-grid census; construction actually separates headers from bodies systematically. The final distribution gate reports generated median object count 4.0.

**Failure mode guarded.** A model might learn “move the one colored block” rather than apply a row-body permutation.

## 8. Make validation task-semantic

**Choice.** `self_check` now rejects malformed cells, ragged or out-of-range grids, zero headers, empty/full bodies, one-header/one-color impostors, and wholly invisible transforms.

**Original rationale.** The old checker skipped all declared degenerates and accepted a full-one-color impostor.

**Alternatives considered.** Shape-only checks; special-case exemptions for degenerate textures; validate only generated instances.

**Probe.** Focused tests mutate valid grids into each structural impostor. Strict defect lint is green.

**Failure mode guarded.** A passing self-check should mean the example actually exercises the selected rule, not merely that it is rectangular.

## 9. Reject unknown overrides before drawing

**Choice.** Validate keyword names against `AXES` and raise `ValueError` with the unknown names.

**Original rationale.** The old `**overrides` path silently accepted typos, making exact-axis claims unfalsifiable.

**Alternatives considered.** Ignore unknown keys for backward compatibility; warn only; depend on `GenCtx` to detect leftovers.

**Probe.** A regression test passes `imaginary_axis=3`; the strict override gate also performs its universal unknown-key probe.

**Failure mode guarded.** A misspelled experiment parameter must not return an ordinary grid and look successful.

## 10. Use executable rivals rather than descriptive claims

**Choice.** Declare four rivals: headers-1-to-4-only, clipping, zero-modulo-moves-one, and first-header-for-all-rows. Each witness claims a named rival and checks actual output disagreement.

**Original rationale.** No semantic hooks existed.

**Alternatives considered.** Boolean feature counters without rival outputs; prose-only notes; one canonical shortcut only.

**Probe.** The semantic gate verified all 4/4 claims and 12/12 lesson windows.

**Failure mode guarded.** A witness can fire frequently while proving nothing if the supposed rival gives the same answer.

## 11. Add task-local regression tests

**Choice.** Add 11 pytest tests in the selected generator's `tests/` directory.

**Original rationale.** No task-local tests existed.

**Alternatives considered.** Depend only on the global battery; create an ad hoc workspace script.

**Probe.** Tests were first observed failing on the imported generator, then all passed after the implementation. The final run is 11/11 green.

**Failure mode guarded.** Global aggregate gates can miss deterministic replay, fresh-object, exact compact counterexample, or local API regressions.
