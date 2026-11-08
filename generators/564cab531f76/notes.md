# Working notes: 564cab531f76

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `ff3ea182557c3b416c53fc656934f1f38b6c1af7cc5b6cc49da09474948ca9d1`.

# Decisions for 564cab531f76

Final generator SHA-256: `ff3ea182557c3b416c53fc656934f1f38b6c1af7cc5b6cc49da09474948ca9d1`.

## D1 — Bind the generator to the unchanged canonical authority

**Decision.** Keep the Racket rule unchanged, set `RULE_HASH = "ef9264e6f3e7"`, and rewrite the generator-facing description and diagnostics around the exact canonical rule: recolor each connected non-corner object by the corner nearest its tight bounding-box center under Manhattan distance; ties resolve in NW, NE, SW, SE order.

**Reason.** The canonical examples and written solution agree, while version 1.4.1 described first-cell/minimum-cell and Euclidean-or-Manhattan alternatives. That was a generator/description defect, not evidence that the authority should change.

**Rejected alternatives.** I rejected preserving the old prose, changing the Racket rule to nearest occupied pixel, and hiding the mismatch behind looser tests. The independent oracle in `workspace/reference_probe.py` matches all four canonical pairs and 28 sampled real-Racket outputs.

**Failure mode guarded.** A future edit that changes center definition, metric, or tie direction fails canonical tests, rival tests, and Racket parity.

## D2 — Remove fake combinatorial axes instead of pretending they work

**Decision.** Advertise only `grid_h`, `grid_w`, and `n_blobs`.

**Reason.** The old `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` controls were fixed, aliased, ignored, or destructive. The baseline override report found 15,997 issues in 74,340 attempts. Honest low-dimensional control is more useful for training and reproducibility than a broad but false interface.

**Range choices.** Dimensions are `6..14`; object count is `2..5`. These ranges admit every joint combination, fit the ARC color budget when four unique corner colors and unique blob colors are used, and include canonical 6×6 scale.

**Rejected alternatives.** I considered retaining palette and texture as diagnostic-only axes, but they did not add semantic variation and would preserve confusing surface API. I also rejected dimensions down to 5 because constructive quadrant support and the four-cell teaching witness become fragile.

**Probe.** `test_all_legal_axis_combinations_are_total_exact_and_deterministic` exhausts 9×9×4 = 324 combinations; four representative corners of the domain are also tested in every difficulty band.

## D3 — Use a five-draw deterministic teaching schedule

**Decision.** Every five consecutive profile residues contain two canonical-scale examples followed by square, wide, and tall strong witnesses.

**Reason.** The baseline had only 3/60 canonical-profile hits and no medium/hard support. Purely random placement also gives no guarantee that a four-example lesson distinguishes canonical-fitting shortcuts. A short deterministic schedule makes lesson composition inspectable and exhaustively testable.

**Intermediate rejected design.** The first repair used only one canonical-scale residue and a larger asymmetric witness. It failed the profile floor at 12/60 (20%) and defect lint because object sizes exceeded canonical support. Evidence is retained in `checks/after-v1/`.

**Final choice.** Two residues use a two-cell canonical-scale domino; three use a four-cell asymmetric witness. Thus 40% of schedule positions are canonical-scale, and any full five-position cycle has three counterexamples to every declared geometry rival.

**Probe.** `test_five_draw_schedule_has_two_canonical_scale_residues_and_three_strong_witnesses` and `test_semantic_contract_is_live_across_each_schedule_cycle` inspect every residue and sixteen cycle alignments.

## D4 — Make tie behavior visible rather than avoiding it

**Decision.** Put the primary object on an exact horizontal or vertical bbox-center tie line in every profile.

**Reason.** Canonical corner ordering matters when a center is tied. Avoiding ties would permit a wrong `>=` rule to survive indefinitely. The strong witness also makes bbox center disagree with top-left, bottom-right, centroid, first-pixel, and nearest-occupied-pixel selectors.

**Rejected alternative.** “Strictly nearest corner only” was rejected because it removes a rule-defining branch and encourages shortcut learning.

**Probe.** `SEMANTIC_WITNESSES["bbox_center_exact_tie"]`, `ties_bottom_right`, and the independent `reference_probe.py` all check this explicitly.

## D5 — Keep objects uniquely colored and mostly simple

**Decision.** Give every corner and blob a distinct nonzero color; use one teaching object plus singleton extras.

**Reason.** The task transformation is geometric assignment, not color-based component disambiguation. Unique colors make 4-connected object extraction exact and keep the corpus focused on the intended abstraction. Singleton extras cheaply cover all target quadrants and multiple object counts.

**Trade-off.** This creates a surface restriction: repeated blob colors, multiple complex blobs, border-touching blobs, and distractors are not generated. This is documented rather than disguised as diversity. A later expansion should add those cases only with new tests showing components remain unambiguous and lesson rivals remain refuted.

**Rejected alternative.** Random grown blobs were rejected because the old implementation made first-pixel/nearest-pixel behavior unpredictable, could accidentally merge components, and did not guarantee semantic counterexamples.

## D6 — Validate the actual task domain, including canonical examples

**Decision.** `self_check` enforces rectangular ARC grids, dimensions 6..14, four distinct singleton corner markers, zero background, 2..5 non-corner components, unique blob colors, and disjoint corner/blob colors. It does not reject a canonical example merely because a non-corner object touches a non-corner border cell.

**Reason.** An earlier draft overconstrained every object to the strict interior. The canonical domain permits non-corner border contact; tests forced the validator to accept authority data rather than an invented narrower rule.

**Rejected alternative.** Keeping “all object cells strictly inside the border” as a validator error was rejected. The generator itself stays interior for construction simplicity, but validator acceptance is broader.

**Probe.** All four canonical pairs pass `self_check`; eight destructive mutations and malformed inputs are rejected diagnostically.

## D7 — Declare rivals that are empirically canonical-fitting

**Decision.** `CANONICAL_SHORTCUTS` contains only rules verified to fit every usable canonical pair: bbox top-left, occupied centroid, first pixel, and nearest occupied pixel under Manhattan or Euclidean distance. `SEMANTIC_RIVALS` adds bbox bottom-right and wrong tie direction; `LESSON_COMPETITORS` adds identity and fixed-corner baselines.

**Reason.** A rival label is useful only when its claimed relationship to canonical data is true. One candidate initially proposed as canonical-fitting was removed after the independent tests showed it failed a canonical pair.

**Rejected alternative.** Copying a static name list into tests was rejected. Tests iterate the generator declarations and independently recompute outputs.

**Probe.** Canonical fit is checked pair-by-pair; every strong schedule draw refutes all seven geometry rivals; production census refutes every declared competitor in all 300 lessons.

## D8 — Add an independent reusable probe, not just implementation-coupled tests

**Decision.** Add `workspace/reference_probe.py` with independent component extraction, bbox-center oracle, rival implementations, distribution measurements, canonical loading, and optional supported Racket execution.

**Reason.** Testing production helpers against themselves can ratify the same mistake twice. The probe is usable by future reviewers from the packet runtime and writes a source-hash-bound JSON report.

**Output.** `checks/reference-probe.json` covers 100 draws each for default/easy/medium/hard and 28 real-Racket comparisons.

**Limit.** It is still authored by this reviewer and uses a finite rival family. The real Racket sample is the authority check; the Python geometry is supplementary.

## D9 — Treat test failures as design evidence

**Decision.** Retain the initial missing-contract failure and the intermediate profile/object-size failure rather than deleting them.

**Reason.** They show the tests were capable of rejecting the old and first-repair behavior. `checks/before/tdd-red.log` records the absent contract; `checks/after-v1/tdd-red-profile.log` records the profile correction.

## D10 — Keep audit findings separate from the selected-task patch

**Decision.** Do not modify audit targets `0d655a5e1a2d` or `a02bd9f85082`.

**Reason.** The assignment requests adversarial findings only. Each finding has a small source/rule-hash-bound reproducer under `checks/audit/`, including supported Racket output where applicable.

## D11 — Final handoff uses exact bytes

**Decision.** Generate a four-file patch from the original ZIP, run `git apply --check`, apply it to a second clean extraction, compare SHA-256, and rerun the 56-test focused suite there.

**Reason.** This catches unrecorded workspace dependencies and report/source drift. The replayed generator hash equals the final checked and solved hash `ff3ea182…`.

**Evidence.** `checks/final-task.patch`, `checks/fresh-replay.log`, and `checks/fresh-replay-focused-tests.log`.
