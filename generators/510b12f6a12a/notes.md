# Working notes: 510b12f6a12a

## 2026-10-02 review — assignment `review-2a1b59831d1ebc25`

### Baseline findings

The imported 2.0.1 sampler omitted color-5 blockers entirely even though blocker stopping is the only nontrivial behavior in two of the three canonical pairs. It therefore taught the simpler Cartesian-product rule. A “use only the first two emitters from each edge” program fits every canonical pair, but the old sampler already refuted it on 67/100 draws in each band (201/300 total). The new curriculum adds deliberate lesson-level extra-emitter witnesses; it does not introduce the first such sampled counterexamples. The generator did not pin `RULE_HASH`; several advertised axes were aliases, singletons, or ignored; `n_h` was not an advertised exact control; `self_check` accepted malformed/impostor grids; and the summary incorrectly said non-crossing output cells preserve the input.

The attempted monolithic baseline battery reached `dist_gate` only after reporting missing `RULE_HASH`, unprobed singleton/dead axes, and texture/degenerate issues. The wrapper timed out and did not retain its temporary stage tree, so the reproducible task-local baseline regression log is retained separately.

### Selected design

- Keep the canonical Racket rule unchanged. Its selected canonical and task-local authority texts are exact, and both selected and archival texts solve every canonical pair.
- Restrict default sizes to the canonical profiles `(8,8)`, `(9,9)`, and `(8,10)` to satisfy morphology support while varying layouts, emitter counts, and blockers.
- Replace metadata/template axes with five literal controls recoverable from pixels: height, width, vertical emitter count, horizontal emitter count, and blocker count.
- Cycle eight deterministic profiles. Nonzero-blocker profiles construct at least one blocker whose removal changes the correct output. Extra-emitter profiles construct at least one output cell missed by the first-two-emitter shortcut.
- Use difficulty only as a profile-cycle phase offset (`easy=0`, `medium=1`, `hard=2`). This gives distinct public bands without changing semantics or weakening exact overrides.
- Declare executable witnesses and rivals: `functional_blocker` versus `ignore_blockers`, and `extra_emitters` versus `first_two_emitters_only`. The latter is explicitly declared as a canonical-fitting shortcut.
- Keep an independent Python beam oracle in `workspace/reference_probe.py`; do not use generator-private helpers for the regression expectations.

### Rejected alternatives

- Random blockers without a semantic check: rejected because blockers can land after all relevant crossings or off both ray families and become decorative.
- Arbitrary larger grids: rejected because the strict profile gate needs reliable canonical morphology support; the rule is already exercised through emitter/blocker variation.
- Preserve the original palette/texture/density axes: rejected because they were aliases or constants rather than observable controls.
- Change the Racket program: rejected because the defect was training-data coverage, not authority behavior.
- Require global uniqueness across episodes: rejected after the 100-lesson probe. The production worker requires uniqueness only inside one episode; cross-episode repeats remain useful distribution evidence, not invalid samples.

### Bounded lesson evidence

`workspace/lesson_probe.py` mirrors the production accepted-prefix episode sampler: one seed per lesson, consecutive sample indices, first four distinct lawful pairs, at most 20 attempted draws. For each difficulty it sampled 100 lessons (400 pairs) from generator SHA-256 `6b6c2d8c633f257d81cd33d08012ca9ef4004c72c88147a9db0a4d422c965540`.

- Easy: 387/400 globally unique inputs; both rivals refuted in 100/100 lessons; zero rejected draws.
- Medium: 394/400 globally unique inputs; both rivals refuted in 100/100 lessons; zero rejected draws.
- Hard: 392/400 globally unique inputs; both rivals refuted in 100/100 lessons; zero rejected draws.

This is bounded separation against the declared rivals, not a claim of universal induction.

### Remaining limitations

The default four-pair lesson sees only four consecutive residues of the eight-profile cycle, so one lesson does not expose every legal count. Across seeds and bands, however, every lesson contains a blocker counterexample and an extra-emitter counterexample. The independent oracle is a second implementation, not a formal proof; official Racket parity remains a separate gate. Global input diversity is high but not perfect because the lawful grid/count domain is intentionally narrow and canonical-shaped.
## Current reviewer considerations

Source SHA-256: `6b6c2d8c633f257d81cd33d08012ca9ef4004c72c88147a9db0a4d422c965540`.

# Decisions — `510b12f6a12a`

All selected choices below apply to generator version `3.0.0`, SHA-256 `6b6c2d8c633f257d81cd33d08012ca9ef4004c72c88147a9db0a4d422c965540`. “Original rationale” means evidence recoverable from the baseline source or notes; where none was recorded, it is marked unknown rather than invented.

## D1 — Repair the generator, not the Racket rule

- **Original rationale:** Unknown. The baseline packet had no evidence that authority behavior was wrong.
- **Selected choice:** Leave the canonical Racket program and canonical examples unchanged; pin `RULE_HASH="8686bcf8a89a"` in the generator.
- **Alternatives considered:** Rewrite the Racket rule; copy the archival implementation into the selected authority; change canonical examples.
- **Probe:** Canonical parity through the independent Python oracle, `rule_smoke`, `racket_lint`, and `authority_sync`.
- **Failure mode addressed:** Data coverage defects being misdiagnosed as solver defects.
- **Limitation:** Execution parity over canonical/generated probes is not a formal equivalence proof. The archival source is textually distinct, though both authority texts solve all canonical pairs.

## D2 — Restrict sizes to exact canonical morphology profiles

- **Original rationale:** The baseline used narrow sizes but did not explain why.
- **Selected choice:** `grid_h=8..9`, `grid_w=8..10`, with default profiles `(8,8)`, `(9,9)`, and `(8,10)`.
- **Alternatives considered:** Broad arbitrary rectangles; only one fixed size; size as an unobservable metadata axis.
- **Probe:** `profile_floor` accepted 3/3 canonical inputs and hit exact/envelope profiles 60/60; task tests exercise both size boundaries.
- **Failure mode addressed:** A semantically rich sampler that fails the canonical morphology floor or drifts away from the task's demonstrated scale.
- **Limitation:** Size diversity is intentionally narrow; most variation comes from layouts, counts, and blockers.

## D3 — Use five literal exact controls and remove aliases

- **Original rationale:** Unknown. Baseline palette/texture/density/position controls were constants, aliases, or unprobed, and horizontal emitter count was not an exact control.
- **Selected choice:** Advertise only `grid_h`, `grid_w`, `n_v`, `n_h`, and `n_blockers`; each is directly recoverable from pixels through `observe_overrides`.
- **Alternatives considered:** Preserve old names for compatibility; advertise schedule profile; retain abstract density/texture knobs.
- **Probe:** Boundary tests in every difficulty; strict unknown/type/range failures; override battery over 143 cases and 12,870 draws.
- **Failure mode addressed:** Claimed controls that do not alter output, cannot be observed, or silently accept illegal values.
- **Limitation:** No soft distribution controls are exposed. Every supported override is exact, so callers wanting style-level sampling must select seeds/indices instead.

## D4 — Generate 2–4 emitters in each family

- **Original rationale:** The baseline stayed at the canonical two-emitter regime; no rationale was recorded.
- **Selected choice:** Support exact `n_v,n_h in 2..4` and include profiles with extra emitters.
- **Alternatives considered:** Keep exactly two; extend to every edge cell; vary only one emitter family.
- **Probe:** `extra_emitters` witness versus `first_two_emitters_only`; canonical shortcut verified to fit all 3 canonical pairs; 403/600 semantic-gate firings and 100/100 lesson refutations per band.
- **Failure mode addressed:** A learner hard-coding the first two emitters while appearing perfect on canonical examples.
- **Limitation:** Counts above four are not trained. The selected range is sufficient to break the observed shortcut without crowding these small grids.

## D5 — Place 0–6 blockers, with nonzero profiles semantically decisive

- **Original rationale:** The baseline advertised/mentioned blockers but emitted none, so the central mechanism had no training support.
- **Selected choice:** Exact `n_blockers=0..6`; when nonzero, placement search requires at least one blocker whose removal changes the correct output. Profiles rotate which ray family receives the first decisive blocker and try to teach both directions.
- **Alternatives considered:** Uniform random interior blockers; blockers only at crossings; always use blockers; no blockers.
- **Probe:** Independent-oracle `functional_blocker` test, `ignore_blockers` rival, semantic gate (464/600 witnesses), and 100/100 lesson refutations per band.
- **Failure mode addressed:** Decorative color-5 cells that increase palette coverage without teaching stopping.
- **Limitation:** Some additional blockers may be nonfunctional after a decisive blocker is guaranteed. The rule permits them, and exact count remains observable.

## D6 — Eight deterministic profiles instead of unconstrained random sampling

- **Original rationale:** The baseline used a template-like schedule but its axes were not semantic and some were dead.
- **Selected choice:** Cycle eight named profiles covering blocker-free anchors, blocked canonical shapes, extra emitters in each family, both extra families, and mixed counts.
- **Alternatives considered:** Pure random counts/layouts; one profile per difficulty; exhaustive Cartesian scheduling.
- **Probe:** Task test covers all profile names and all three canonical morphology profiles; semantic gate reports every profile in every band; lesson probe records profile counts.
- **Failure mode addressed:** Rare or seed-fragile semantic witnesses and profile-floor misses.
- **Limitation:** Four-pair lessons see only half the cycle. They are nevertheless constructed so each lesson contains both declared shortcut counterexamples; the full legal control range appears across lessons rather than inside each lesson.

## D7 — Difficulty changes curriculum phase only

- **Original rationale:** Unknown. The first repair accidentally made easy/medium/hard byte-identical.
- **Selected choice:** Shared eight-profile cycle with offsets `easy=0`, `medium=1`, `hard=2`; exact overrides and the rule remain identical.
- **Alternatives considered:** Ignore difficulty; increase semantic complexity/ranges by band; use a difficulty-specific random distribution.
- **Probe:** A test was written first and failed (`checks/difficulty_dead_band_red.log`); the minimal phase-offset change made it pass (`checks/difficulty_dead_band_green.log`) and final defect lint is green.
- **Failure mode addressed:** A declared difficulty interface that has no observable effect.
- **Limitation:** Difficulty is a curriculum ordering signal, not a calibrated monotonic hardness score.

## D8 — Declare executable witnesses and plausible rivals

- **Original rationale:** Baseline had no semantic contract.
- **Selected choice:** `functional_blocker` versus `ignore_blockers`; `extra_emitters` versus `first_two_emitters_only`; declare the latter under `CANONICAL_SHORTCUTS` and both under `LESSON_COMPETITORS`.
- **Alternatives considered:** Prose-only semantics; arbitrary rivals not known to fit canonical data; rely on output diversity alone.
- **Probe:** Semantic gate verifies 2/2 witnesses and 2/2 rival claims; task tests independently compute correct outputs; lesson probe iterates the actual declarations rather than a copied name list.
- **Failure mode addressed:** Passing morphology/diversity checks while teaching a simpler rule.
- **Limitation:** The competitor list is not exhaustive. A novel shortcut may still exist.

## D9 — Keep an independent oracle and source-bound production-sampler audit

- **Original rationale:** Unknown. Baseline tests reused generator assumptions and no 100-lesson evidence was retained.
- **Selected choice:** `workspace/reference_probe.py` implements the beam rule independently. `workspace/lesson_probe.py` mirrors production's accepted-prefix sampling and hashes the exact generator source.
- **Alternatives considered:** Call generator-private `rule_mirror` as the expected value; sample isolated pairs rather than assembled lessons; demand global uniqueness across episodes.
- **Probe:** 100 lessons × 4 pairs × 3 bands, zero rejected draws, source hash recorded; both rivals refuted in every lesson. Task-local policy test confirms cross-lesson repeats are reported but not treated as within-episode violations.
- **Failure mode addressed:** Self-confirming tests, unbound evidence, and pair-level witness counts that fail to establish complete-lesson support.
- **Limitation:** Independent code can share conceptual mistakes; official Racket parity remains a separate gate. Results are bounded to the sampled seeds, declared rivals, and exact final source hash.

## D10 — Verify repository tests in fresh module processes

- **Original rationale:** Not a generator design choice; introduced as a verification workaround after shared-process Racket lifecycle stalls.
- **Selected choice:** Add `checks/run_isolated_repo_tests.py`, running each of the 23 repository test modules in a fresh supervised process with a 300-second module timeout and process-group cleanup.
- **Alternatives considered:** Call the partial monolithic dot stream a pass; omit repository testing; modify shared test/runtime code outside assignment scope.
- **Probe:** `checks/repo_tests_isolated.json`: 23/23 modules, 174/174 tests, zero failures/skips/timeouts.
- **Failure mode addressed:** Losing attribution and completed evidence when a shared Racket-backed pytest process stalls.
- **Limitation:** This verifies the same tests under stronger process isolation; it does not fix the underlying monolithic lifecycle problem, which is reported in `FEEDBACK_TO_CODEX.md`.
