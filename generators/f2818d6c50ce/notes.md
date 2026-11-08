# Working notes: f2818d6c50ce

## Review `review-6f4e0d954f1fab47`

### Authority

- Canonical rule retained unchanged.
- Final generator pins `RULE_HASH = 216362042c61`.
- Final generator SHA-256: `46985b7b1b8a22cc239ed7003bd9f4c1eb886406521df43981d9ed7ed7522665`.
- Rule smoke: 120/120 applied, zero crashes, 57 distinct outputs, A-B-A reentrant.
- Selected authority synchronization and execution parity pass; one archival raw source remains divergent and was not selected.

### Baseline defects

- Missing `RULE_HASH`.
- Canonical profile floor: exact 2/60, envelope 5/60; medium and hard had zero support.
- No `strict_canonical_like`, semantic witnesses, rivals, or lesson-identifiability hook.
- 9,460 override findings over 59,940 draws/666 cases, including silently accepted unknown keys and band-dependent rejections/clamping.
- Every foreground color was an exact pair, so “all nonzero colors contribute bars” fit the generated data.

### Distribution decisions

- Replaced texture controls with exact axes: grid height/width 8..22, pair count 1..6, distractor-color count 0..2.
- Added a three-example schedule: canonical, singleton distractor, mixed distractors.
- Canonical branch exactly anchors the three public dimensions, three pair colors, no distractors, and observed span profiles.
- Non-pair colors occur once or three times and are ignored by the selected rule.
- Constructive cached candidate placement guarantees aligned, non-overlapping pair endpoints.
- Equal-span lessons require at least three pairs with another distinct length, avoiding all-solid multirow outputs.

### Semantic contract

- Rival: `all_nonzero_colors_are_pairs`.
- Witness: `ignore_nonpairs`.
- `lesson_identifiable` requires every declared competitor to lose on at least one demonstration.
- `EXAMPLES_NEEDED = 3`; `MIN_STRICT_FRAC = 0.25`.

### Final evidence

- Exact after battery: 12/12 green.
- Task-local tests: 23/23 passed.
- Profile floor: exact/envelope 18/60.
- Semantic gate: strict 181/600; witness 419/600; rival claim 60/60; lessons 12/12.
- Override contract: 49,950/49,950 accepted, 555 cases, zero findings.
- Source-bound curriculum audit: 300/300 lessons identifiable, 1,200/1,200 unique inputs, 798 rival disagreements, zero surviving windows.

### Failed iteration retained

The first tie implementation allowed two equal spans, producing a solid `2×L` output. A failing regression and strict-defect evidence are retained under `checks/tdd/degenerate_tie_red.txt` and `checks/after-defect_lint/`. The final implementation requires a third, different span.

### Future checks

- Run lesson-window rival survival on the actual packed/sharded order, not only generator order.
- Add new executable rivals when model failures reveal recurring shortcuts.
- Re-run the source-bound auditor after any schedule, rival, or rule-hash change.
- Do not infer universal identifiability from the current single-rival contract.
## Current reviewer considerations

Source SHA-256: `46985b7b1b8a22cc239ed7003bd9f4c1eb886406521df43981d9ed7ed7522665`.

# Distribution and implementation decisions

## D1 — Pin the selected authority; do not edit Racket

**Choice.** Added `RULE_HASH = "216362042c61"` and kept the canonical Racket program byte-for-byte unchanged.

**Rationale.** Rule smoke and authority synchronization already showed correct selected behavior; the defect was generator coverage and contract quality, not the oracle. Editing a working authority would add risk without improving the lesson distribution.

**Rejected alternatives.** Rewriting the Racket for style; changing the output definition; silently accepting the missing pin.

**Probe/evidence.** `checks/after/checks/f2818d6c50ce_after_rule_smoke.log`, `checks/after/checks/f2818d6c50ce_after_authority_sync.log`.

**Limitation.** The canonical source retains one style-only `dummy-let-binding` report.

## D2 — Replace textures and band-limited controls with four exact axes

**Choice.** The public surface is exactly `grid_h=8..22`, `grid_w=8..22`, `n_pairs=1..6`, and `n_distractor_colors=0..2`.

**Original rationale.** Unknown. The imported version exposed texture controls and broad ranges that were clamped, inert, or rejected in some bands.

**Rationale.** Each retained axis is observable from returned pixels, valid in every difficulty band, and honored constructively in every combination. Difficulty changes sampling bias only; it does not narrow the override domain.

**Rejected alternatives.** Band-specific “valid” ranges; hidden clamping; declaring thousands of ordinary combinations incompatible; retaining texture labels that do not identify a unique materialized grammar.

**Probe/evidence.** Baseline `checks/before-override/`; final `checks/after/checks/f2818d6c50ce_after_override.log`.

**Failure mode guarded.** A caller requests `grid_h=22` in easy mode or mistypes an axis and receives a plausible but different grid.

## D3 — Use a constructive pair placer

**Choice.** Enumerate all aligned endpoint pairs for a requested span and place non-overlapping pairs with deterministic backtracking.

**Rationale.** A retry sampler makes exact overrides probabilistic, can become slow in dense scenes, and obscures why a combination failed. The candidate cache plus bounded backtracking guarantees requested dimensions, pair count, and spans whenever they are in the declared domain.

**Rejected alternatives.** Randomly draw endpoints until enough happen to align; clamp pair count; resize the grid after a failed placement.

**Probe/evidence.** Task-local tests in `repo/generators/f2818d6c50ce/tests/`; override gate accepted 49,950/49,950 draws.

**Limitation.** This is optimized for at most six pairs on 8–22 grids; it is not a generic large matching engine.

## D4 — Preserve canonical anchors explicitly

**Choice.** Every third default example uses one of `(10,10)`, `(11,11)`, or `(10,12)`, three pair colors, no distractors, and one of the observed canonical span patterns.

**Rationale.** The baseline had only 2/60 exact-profile and 5/60 envelope support, with no support in medium or hard. A deterministic anchor avoids relying on low-probability coincidence.

**Rejected alternatives.** Merely increase the chance of 10–12 grids; copy the exact canonical grids verbatim; make every example canonical-like.

**Probe/evidence.** `checks/before-profile_floor/` versus `checks/after/checks/f2818d6c50ce_after_profile_floor.log`.

**Limitation.** Canonical-like does not mean exact canonical instance; positions and colors remain varied.

## D5 — Add lawful non-pair colors as semantic counterexamples

**Choice.** The two noncanonical branches add one singleton, or a singleton plus a three-cell color. The selected rule ignores both.

**Rationale.** All public examples and the imported generator made every foreground color occur exactly twice. The rival “emit a bar for every foreground color” therefore fit the data. Multiplicities 1 and 3 are the cheapest unambiguous way to teach the exact-two filter without changing the authority.

**Rejected alternatives.** Noise colors that accidentally occur twice; output-side annotations; unlabelled random clutter; only singletons (which would not test counts above two).

**Probe/evidence.** `checks/after/checks/f2818d6c50ce_after_semantic_gate.log`; `checks/final-curriculum-audit.json`.

**Failure mode guarded.** A model generalizes “one bar per visible color” rather than “one bar per color occurring exactly twice.”

## D6 — Three-profile lesson schedule

**Choice.** Cycle `canonical`, `singleton_distractor`, and `mixed_distractors`; `EXAMPLES_NEEDED = 3`.

**Rationale.** Every consecutive three-example lesson contains scale/morphology anchoring plus at least one shortcut-refuting example. Deterministic scheduling makes coverage testable and cheap.

**Rejected alternatives.** Independent random branch probabilities; all-distractor lessons; a longer cycle than the lesson size.

**Probe/evidence.** `audit_curriculum.py` checks all cyclic starts, 100 lessons per band. Final result: 300/300 identifiable.

**Limitation.** Any deterministic modulo schedule can alias with a matching data-loader stride. The new auditor checks cyclic starts but not every external sharding implementation; the `bab4d8f5ba7a` audit demonstrates why the packer should also be tested.

## D7 — Avoid the two-equal-bars solid-rectangle degenerate

**Choice.** Equal spans are generated only when at least three pairs exist, and at least one pair has a different span.

**Rationale.** Two equal spans produce a completely solid `2×L` output. It is lawful but low-information and was correctly flagged by strict defect lint.

**Rejected alternatives.** Suppress all ties; accept solid outputs; add a cosmetic zero column not justified by the rule.

**Probe/evidence.** Failing regression `checks/tdd/degenerate_tie_red.txt`; failed strict run `checks/after-defect_lint/`; final green suite and battery.

## D8 — Build a source-bound curriculum auditor

**Choice.** Added `workspace/audit_curriculum.py` rather than only describing future analysis.

**Rationale.** The repository semantic gate samples 12 lessons, which is an appropriate smoke test but not enough to establish schedule-wide coverage. The tool reads the generator’s own rival declarations, verifies canonical shortcut applicability, tests all cyclic starts, and records source hash, seeds, denominators, unique inputs, and rival disagreements.

**Rejected alternatives.** Hard-code a rival-name list in a one-off notebook; count witness frequency without assembling lessons; report pooled examples as independent lessons.

**Probe/evidence.** `checks/final-curriculum-audit.json` and `.log`.

## D9 — Audit targets remained unchanged

The two drawn audit targets were inspected adversarially but not patched, as required. `AUDIT.md` separates distribution risks, authority/test defects, validator status, and live-Racket evidence. Their source hashes still match `AUDIT_ASSIGNMENT.json`.
