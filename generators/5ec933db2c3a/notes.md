# Working notes: 5ec933db2c3a

## Review 2026-10-07

The imported `2.1.0` generator was not source-linked to the selected rule. It generated arbitrary single-color 3–5-cell motifs with approximately one missing cell, while the authority and canonical pairs use a fixed two-color 3×3 template, four rotations, and exactly two missing occupied cells. Its validator rejected all three canonical pairs, its advertised axes were largely dead or false, and it did not pin `RULE_HASH`.

The replacement is intentionally narrow and authority-derived rather than a repair of the old motif grammar. It keeps the canonical template/colors, validates the exact match predicate, emits two true targets plus one-hole and three-hole negatives, requires rotation, and makes color preservation observable. Random construction is checked by the exact scanner; a deterministic local-search fallback prevents weak samples from escaping.

Only dimensions remain public axes. Template orientation, target rotations, missing-cell locations, and role placement are seeded nuisance variation, not advertised controls. Canonical dimensions are scheduled on three of four samples to keep every difficulty band close to the owned corpus while the fourth profile expands scale.

The selected Racket authority was not changed. Final generator SHA-256: `32378ad32e0d4ab2500adf5792c024646274dd32b46364185e7521b7cd1d9315`.

Limits: the finite semantic contract distinguishes three declared plausible rivals, not every possible hypothesis. The generator intentionally fixes semantic colors and template topology; palette permutations, reflections, extra noise, and noncanonical templates were rejected because the selected authority does not establish those as interchangeable.
## Current reviewer considerations

Source SHA-256: `32378ad32e0d4ab2500adf5792c024646274dd32b46364185e7521b7cd1d9315`.

# Decisions: 5ec933db2c3a

## D1 — Keep the selected authority unchanged

**Decision.** Preserve the selected Racket rule and canonical row, pin `RULE_HASH = "009a49ded011"`, and repair only the Python generator and task-local support files.

**Why.** All canonical pairs are internally coherent and the selected rule has a clear active branch: split at the full-height color-9 divider, crop the two-color template, scan four rotations, and repair only exactly-two-hole windows. Rule smoke and authority synchronization already worked at baseline. The defect was that the imported generator represented a different task.

**Rejected alternative.** Generalizing the Racket rule to arbitrary motifs or one-hole completion would have changed the owned task to match the broken generator rather than fixing the generator.

**Probe.** Canonical equality is tested independently in `repo/generators/5ec933db2c3a/tests/test_generator_5ec933db2c3a.py`; final rule-smoke and authority-sync evidence is under `checks/after/checks/`.

## D2 — Use the canonical semantic template, not an arbitrary-shape family

**Decision.** Generate the asymmetric 3×3 template with six color-2 cells and one color-7 cell; allow seeded rotation of its displayed orientation but no topology or palette substitution.

**Why.** The canonical data and selected authority establish this template and these semantic colors. The color-7 cell is essential: without making it missing in a target, a solver can fill every hole with color 2 and still fit most samples.

**Rejected alternatives.** Random polyominoes, palette permutations, reflections, and added distractor colors were rejected because no source-bound evidence says the rule is invariant to them. They would increase visual diversity while weakening authority fidelity.

**Failure mode controlled.** A fixed template can invite memorization. The repair offsets this with random displayed orientation, target rotations, hole locations, target/negative corner assignment, vertical template placement, and grid dimensions. The retained claim is task fidelity, not broad shape generalization.

## D3 — Put separating counterexamples inside every input

**Decision.** Every board contains exactly four isolated 3×3 placements: two exact-two-hole targets, one one-hole negative, and one three-hole negative. At least one true target is rotated relative to the displayed template and has the color-7 cell missing.

**Why.** This makes three nearest shortcuts observable in every labeled pair: repair any near-copy, ignore rotations, and recolor all holes red. The exact scanner validates the entire board before return so shifted windows cannot create accidental extra targets.

**Rejected alternative.** Sampling positives and negatives independently across examples could make individual lessons fail to distinguish a rival. Per-input separation gives stronger local evidence and makes any three-example lesson robust to ordering.

**Probe.** `test_generated_inputs_have_exact_targets_and_all_three_counterexamples` and the 1,500-draw stress probe check the complete scene, not just intended placements.

## D4 — Advertise only exact, useful controls

**Decision.** Retain `grid_h` and `grid_w` as the only public axes. Validate type/range/unknown keys before generation and implement exact observation with `observe_overrides`.

**Why.** The old metadata advertised palette, density, texture, shape count, and related controls that were dead, singleton, or incompatible with the actual rule. Template orientation, role placement, rotation, and holes are useful randomness but not user-facing independent axes.

**Rejected alternative.** Exposing every nuisance variable would enlarge the override matrix without improving curriculum design and would let callers request weak lessons, such as no rotation or no color-role witness.

**Probe.** The exhaustive override gate passed 2,700/2,700 accepted cases with no findings; invalid and unknown requests are covered by task tests.

## D5 — Bias default profiles toward the canonical support

**Decision.** Schedule exact canonical dimensions on three of every four samples, with a fourth difficulty-aware expansion profile.

**Why.** The baseline missed canonical object/profile support. The schedule guarantees every 20-draw band sample hits owned dimensions while retaining scale diversity. Default bounds are deterministic by `sample_index`; randomness remains inside each profile.

**Rejected alternative.** Uniform sampling over all 20 dimension pairs can pass overall diversity while occasionally missing canonical support in a small band sample. Using only canonical dimensions would eliminate useful scale variation.

**Probe.** The profile-floor test and final battery pass; the task test pins canonical support in every difficulty band.

## D6 — Make lesson identifiability executable

**Decision.** Declare three semantic rivals, three witnesses, witness-to-rival links, the same lesson competitors, and a `lesson_identifiable` hook requiring at least three demonstrations and refutation of every competitor.

**Why.** Correct labels alone do not ensure the intended rule is learnable. This task's old generator was especially vulnerable to hole-count, orientation, and color-role shortcuts.

**Lesson policy measured.** Production assembly used three demonstrations plus one query. A source-bound census covered 300 lessons (100 per band) and all four possible query positions under required rotation: 0/300 production ambiguity and 0/1,200 rotated ambiguity, with 1,200 unique inputs.

**Limit.** These are finite checks against declared hypotheses, not a proof of unique induction. No claim is made about undeclared programs or schedules outside the sampled production policy.

## D7 — Add a portable independent test suite

**Decision.** Add tests under the selected task's `tests/` directory using `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`, plus an independent oracle rather than assertions against the generator's own mirror.

**Why.** The general battery does not automatically discover task tests, and self-consistency tests can preserve the same bug in implementation and expectation. The independent oracle checks canonical and generated semantics, while mutation tests ensure rule/rival calls are pure.

**Measured result.** The test-first run failed 61 tests on the imported generator; the final isolated task-test runtime passed 62/62.

## Reusable artifacts

The most reusable artifact is the task-local regression suite itself. It provides a compact independent oracle, complete scene classifier, lesson-window rival check, exact override matrix, and malformed-grid diagnostics. No shared repository tool was modified; shared-tool suggestions are isolated in `FEEDBACK_TO_CODEX.md`.
