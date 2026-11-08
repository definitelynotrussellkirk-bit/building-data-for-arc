# Working notes: 93b39d8c4da4

## 2026-10-03 repair (`review-c5786b3e2c8699ee`)

- Pinned canonical `RULE_HASH = d20fb64e7b01`; the Racket authority was not edited.
- Replaced dead/overlapping texture controls and heuristic placement with five exact observable axes: `grid_h`, `grid_w`, `template_id`, `n_marks`, `layout_mode`.
- Constructive finite backtracking makes every advertised boundary combination feasible in every difficulty band.
- Added an 18-shape connected template bank, including normalized shapes with an empty `(0,0)` cell.
- Added a four-profile source schedule: `canonical_profile`, `offset_anchor`, `many_marks`, `overlap`.
- Declared executable semantic rivals/witnesses and a complete-lesson `lesson_identifiable` contract.
- Added selected tests and `workspace/qualify_distribution.py`, which discovers the live declarations instead of hardcoding rival names.

Final source SHA-256: `1a96c0f22e24c4f68622675e5b96865edba6e8781da9192dcee68feacf43cb1e` before documentation-only changes. Generator bytes remain the same after these notes.

Final measurements:

- aggregate battery: 12/12 green;
- selected portable tests: 11/11 passed;
- qualification probe: 300/300 complete lessons identifiable, 1,500/1,500 unique inputs, zero self-check failures;
- canonical-fitting shortcuts: `first_four_marks_only` and `discard_overlapping_stamps` both fit all six canonical pairs and are rebutted once per four-slot schedule.

See packet-level `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, and `checks/93b39d8c4da4_final_300_lesson_probe.json` for exact commands and evidence.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1a96c0f22e24c4f68622675e5b96865edba6e8781da9192dcee68feacf43cb1e`.

# Decisions for `93b39d8c4da4`

This document separates observed baseline behavior from the choices made in this review. The canonical transformation was treated as fixed: tightly crop the color-2 template, stamp it in color 8 at every color-3 cell using the template bounding-box origin, union overlapping copies, and return a fresh blank-sized canvas. The Racket authority was not edited.

## D1 — Replace nominal texture knobs with semantic exact axes

**Observed baseline.** The previous source advertised controls that did not correspond to meaningfully distinct output behavior. The linter identified a singleton `n_distinct_colors`; defect lint identified four dead texture controls and one overlapping texture domain. No retained rationale explained why those names were preferable to task-semantic controls.

**Choice.** Publish five exact, observable axes: `grid_h`, `grid_w`, `template_id`, `n_marks`, and `layout_mode`.

**Alternatives rejected.**

- Keep decorative density/color knobs and merely suppress linter warnings. Rejected because the canonical grammar fixes input colors to 0/2/3 and the lesson-relevant distinctions are shape, number of marks, and overlap.
- Expose random seed substreams or placement style as public controls. Rejected because they are diagnostics, not stable semantic promises.
- Use only one composite `profile` axis. Rejected because maintainers need independently testable boundary controls, while profiles are better used as a lesson schedule.

**Probe.** `checks/after/checks/93b39d8c4da4_after_override_results.json` exercises all exact public controls across all bands; `observe_overrides()` recovers the realized values. The focused tests cover both endpoints and every template member.

**Failure modes considered.** Fake exactness, accepted-but-ignored overrides, incompatible boundary combinations, an overlap label with no actual overlap, and observational aliasing.

**Limitation.** `template_id` is tied to the declared 18-shape bank. Expanding or reordering that bank is a versioned contract change.

## D2 — Use constructive placement rather than retry-only random sampling

**Observed baseline.** The old sampler depended on heuristic random placement and did not make the full advertised cross-product a proven domain. Its exact override gate generated thousands of rejections and accepted unsupported keys.

**Choice.** Enumerate lawful anchors and use bounded finite backtracking. `separated` requires disjoint stamp sets; `overlap` first chooses an actually intersecting pair and then extends the mark set while preserving mask isolation and all in-bounds constraints.

**Alternatives rejected.**

- Increase retry counts. Rejected because success would remain probabilistic and exact boundary cases could still be unconstructive.
- Generate a scene and then relabel its observed mode. Rejected because an exact override must control behavior, not report whatever happened.
- Permit declared incompatible combinations. Rejected after a constructive search showed the entire advertised cross-product is feasible, so incompatibility declarations were unnecessary.

**Probe.** `test_all_exact_axis_boundaries_are_constructive_and_observable` and `test_every_template_bank_member_is_constructive_in_both_layout_modes`; final override battery accepted 21,960 lawful draws across 24,420 cases with no finding category.

**Failure modes considered.** Exponential search, duplicate marks, adjacent marks merging into one component, overlap with the source template, out-of-bounds stamps, and a nominal overlap pair whose templates do not intersect.

**Limitation.** First-solution backtracking is deterministic after the keyed shuffle rather than uniformly sampling all valid layouts. Uniformity is not claimed; diversity and semantic coverage are measured instead.

## D3 — Preserve canonical support in every difficulty band

**Observed baseline.** Source-bound profile checks showed weak support for canonical dimensions/palette behavior, and the assignment explicitly requires at least one canonical-profile hit in each band’s 20 draws.

**Choice.** Keep the full axis ranges legal in every band, use difficulty only as a weighting preference, and schedule a `canonical_profile` every four sample indices. Canonical profile dimensions come from the six observed canonical dimension pairs and use canonical template/mark regimes.

**Alternatives rejected.**

- Partition dimensions by difficulty (small/easy, large/hard). Rejected because it can make the hard band incapable of producing canonical-size lessons.
- Emit exact canonical inputs verbatim. Rejected because memorized inputs add no new support and reduce diversity; the profile should match the grammar, not copy the instances.
- Treat pooled support across bands as sufficient. Rejected because a learner or evaluator can consume bands independently.

**Probe.** Final profile-floor exact hits: easy 5/20, medium 6/20, hard 7/20; all six canonical inputs accepted. The 300-lesson probe records broad dimensions in every band while preserving 125 `canonical_profile` pairs per band.

**Failure modes considered.** Canonical support only in easy, palette drift, template-bank drift, and profile labels that are not observable from generated data.

**Limitation.** Difficulty bands are distribution weights, not disjoint complexity classes. Exact overrides deliberately remain valid everywhere.

## D4 — Choose an 18-member connected template bank

**Observed canonical grammar.** Canonical templates contain 3–5 color-2 cells, are 4-connected, and include shapes with different bounding boxes. The canonical demonstrations do not settle whether an anchor is the bounding-box origin or the first occupied template cell because most shapes occupy `(0,0)` after normalization.

**Choice.** Include the five canonical shapes plus 13 connected lawful extensions, including several normalized shapes that omit `(0,0)`.

**Alternatives rejected.**

- Use only the five canonical shapes. Rejected because it would preserve a strong first-occupied-cell shortcut and under-sample lawful shape variation.
- Generate arbitrary connected polyominoes online. Rejected because stable `template_id` observation and exhaustive boundary tests are much clearer with a fixed bank.
- Add disconnected templates. Rejected because the canonical object is one connected color-2 template and disconnected templates introduce a different extraction problem.

**Probe.** Every bank member is constructed in both layout modes and passes `self_check`. `bbox_anchor_matters` disagrees with `anchor_first_occupied` 218/500 easy pairs, 200/500 medium pairs, and 209/500 hard pairs in the final probe.

**Failure modes considered.** Duplicate shapes under exact coordinates, disconnected entries, shapes outside the 3–5-cell grammar, and members impossible to place on minimum grids.

**Limitation.** The bank is not an exhaustive set of all 3–5-cell polyominoes up to symmetry. It is a tested teaching domain, not a completeness claim.

## D5 — Allow 2–7 masks and explicitly schedule 5–7

**Observed canonical grammar.** The six canonical pairs contain at most four masks, so a rule that processes only the first four fits all demonstrations.

**Choice.** Declare `n_marks=2..7` and schedule a `many_marks` profile that uses 5–7 masks once every four sample slots.

**Alternatives rejected.**

- Keep the canonical 3–4 range. Rejected because it never distinguishes the intended “every mask” quantifier from a four-mask cap.
- Add only five marks. Rejected because 6–7 are cheap lawful extensions and make the public exact control meaningful.
- Randomly hope for a fifth mark. Rejected because complete-lesson identifiability needs a source-bound guarantee.

**Probe.** `first_four_marks_only` fits all six canonical pairs. The final 300-lesson probe produced exactly 125 fifth-mark witnesses per band and every tested lesson was identifiable. The exact retained counterexample is `checks/question/counterexample.json`.

**Failure modes considered.** Fifth mark stamp fully covered by earlier stamps (no observable disagreement), marks merging by adjacency, and excessive marks making minimum grids infeasible.

**Limitation.** The contract tests “every mask” through seven marks, not an unbounded count. ARC grid limits make an unbounded claim inappropriate.

## D6 — Make overlap a first-class semantic mode

**Observed canonical grammar.** All canonical stamp sets are disjoint, so “skip an overlapping stamp” or “do not union intersections” can fit all canonical pairs.

**Choice.** Add exact `layout_mode=separated|overlap`. In overlap mode at least one pair of complete stamp sets intersects; the expected output is their set union.

**Alternatives rejected.**

- Allow accidental overlap without labeling it. Rejected because it cannot guarantee a lesson-level witness.
- Permit adjacent mask cells to force overlap. Rejected because the input grammar requires isolated color-3 masks and adjacent marks would collapse into a different visual object.
- Use clipping at grid edges as the union witness. Rejected because clipping introduces an extra boundary interpretation; all stamps remain in-bounds.

**Probe.** `discard_overlapping_stamps` fits all six canonical pairs. The final probe records 125 overlap witnesses/disagreements per band, and exact override tests verify the observed mode.

**Failure modes considered.** Overlapping bounding boxes without overlapping occupied cells, complete containment that produces no rival disagreement, and source-template interference.

**Limitation.** The witness targets set-union semantics. It does not separately teach multiplicity because ARC colors carry no count.

## D7 — Four-profile cyclic lesson schedule

**Choice.** Set `EXAMPLES_NEEDED=4` and cycle `canonical_profile`, `offset_anchor`, `many_marks`, `overlap` by `sample_index % 4`. Every four consecutive demonstrations therefore contain one example from each profile, regardless of seed or starting residue.

**Alternatives rejected.**

- Independent profile sampling. Rejected because nonzero marginal witness frequency does not prove each complete lesson contains the witness.
- A longer schedule. Rejected because four examples are sufficient to cover the three rivals plus a canonical anchor; longer lessons would increase cost without a demonstrated need.
- Encode profile selection in the seed. Rejected because cyclic-start coverage becomes harder to inspect and reproduce.

**Probe.** `test_every_four_demo_window_refutes_all_declared_lesson_competitors` tests every cyclic start. The reusable qualification tool tests all residues equally (25 lessons per start per band) and reports 300/300 identifiable lessons.

**Failure modes considered.** Off-by-one windows, seed-dependent schedule drift, a demo profile whose instance does not actually activate its witness, and stale hardcoded rival lists in the probe.

**Limitation.** Identifiability is defined against the declared competitor family, not every mathematically possible program.

## D8 — Declare executable rivals and witnesses

**Choice.** Define three real rival transformations (`first_four_marks_only`, `discard_overlapping_stamps`, `anchor_first_occupied`), three witness predicates, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `WITNESS_RIVALS`, and `lesson_identifiable()`.

**Alternatives rejected.**

- Document shortcuts only in prose. Rejected because prose drifts and cannot be exercised by the semantic gate.
- Use witness predicates without rival outputs. Rejected because “interesting feature present” is weaker than an actual output disagreement.
- Claim the anchor rival is canonical-fitting. Rejected: it is plausible, but some canonical shape arrangements can already expose it; only the first two were verified to fit all six canonical pairs.

**Probe.** The reusable probe discovers declarations live, verifies every claimed canonical shortcut against all canonical pairs, and reports per-band disagreement counts. Semantic gate strict rate is 600/600.

**Failure modes considered.** A named shortcut that does not actually fit canonical data, a witness that is true but leaves outputs equal, and a competitor that survives all demonstrations but changes the query.

**Limitation.** The competitor set is deliberately small and task-specific. It supports a falsifiable curriculum claim, not universal program synthesis.

## D9 — Strict validation and fresh-output purity

**Choice.** `self_check()` rejects malformed dimensions, foreign colors/types, missing or multiple templates, out-of-bank shapes, wrong mask counts, out-of-bounds stamps, adjacent masks, and mask/template contact. `generate()` rejects unknown difficulty and overrides before drawing. `rule_mirror()` returns a new 0/8 grid and does not mutate input.

**Alternatives rejected.**

- Let the Racket rule define behavior on malformed inputs. Rejected because oracle executability is not lesson validity.
- Coerce booleans or numeric strings. Rejected because exact controls should fail closed.
- Accept a superset of shapes in `self_check` while generating a bank subset. Rejected because `strict_canonical_like` is intended to match the advertised training distribution exactly.

**Probe.** Targeted malformed-input and purity tests; final self-check, grammar, lint, and defect-lint stages all green.

**Failure modes considered.** Python `bool` passing as `int`, ragged rows, foreign colors, mutable return aliases, and output retaining source colors.

**Limitation.** Strict validation intentionally rejects lawful variants outside this generator’s declared bank; that is a training-domain boundary, not a claim that the Racket rule cannot execute them.

## D10 — Keep the Racket authority unchanged

**Observed evidence.** Baseline and final rule smoke passed; the Python mirror agreed with every canonical pair; supported Racket application agreed with the intended output on the retained shortcut counterexample. The selected canonical/target authority was synchronized. A distinct archival raw source remains intentionally divergent but execution-equivalent.

**Choice.** Modify only the generator, tests, notes/workspace artifacts. Do not rewrite the canonical or base selected rule.

**Alternatives rejected.**

- Normalize archival source text to silence a diagnostic. Rejected because source-role divergence is pre-existing and execution parity passes.
- Add special cases to the Racket rule for generated profiles. Rejected because profiles are all ordinary instances of the unchanged canonical transformation.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` stages all green; `checks/question/racket.json` records rule and generator hashes for the exact counterexample.

**Limitation.** The Python mirror is a test oracle, not the authority. Racket remains the source of truth for supported execution checks.

## D11 — Build a reusable qualification probe

**Choice.** Add `workspace/qualify_distribution.py` with a stable JSON report. It loads the generator by path, discovers declarations, reads canonical pairs from the supplied ledger, tests all cyclic starts, uses independent lesson seeds, and reports both overlapping windows and unique generated inputs.

**Alternatives rejected.**

- One-off notebook or shell snippets. Rejected because future agents need a rerunnable artifact.
- Hardcode current rival names. Rejected because declarations can evolve independently.
- Count individual witnesses only. Rejected because witness frequency does not prove complete lessons are identifiable.

**Probe.** Test-first absence failure in `checks/tdd-probe-red/pytest.log`, then green selected test and a 300-lesson run in `checks/93b39d8c4da4_final_300_lesson_probe.json`.

**Failure modes considered.** Stale declaration names, treating duplicate inputs as independent evidence, skipping cyclic starts, and claiming Racket parity from a Python-only bulk census.

**Limitation.** Bulk outputs use `rule_mirror` for speed; Racket parity is checked separately through the supported `apply` and battery commands.

## D12 — Add a native episode-fixed template-transform family

**Choice.** Preserve the exact canonical identity program (`d20fb64e7b014794b1e36c0f5b98545b0043a1398faa1bb12bce3bdb3840414d`) and add two private settings: tight-normalized left/right mirroring and clockwise rotation of the input-derived color-2 template before color-8 stamping.

**Reason.** The parameter changes a meaningful geometric operation while preserving the original extraction/stamping structure. Inputs are matched across settings, use 2–6 demonstrations and 1–4 queries independently, include four fixed novel queries up to 30×30, boundary markers, asymmetric templates, and overlapping stamps. The public projection exposes one input-only query and hashes only visible bytes.

**Sequential dependency.** Step A extracts and transforms the complete input template. Its transformed occupied-cell geometry is the intermediate consumed by Step B at every marker. A fixed-L wrong-intermediate program changes the final protected-Racket output on the qualified mirror case.

**Evidence.** Focused tests 26/26; bounded self-audit 12/12 jobs with no surviving named rival; native qualification 6/6 jobs and 60 protected-Racket evaluations; changed-target tests 37/37; causal witness `checks/93b39d8c4da4/causal/witness.json`; inventory `workspace/parametric/evidence/manifest.json`.

**Limit and next action.** Evidence is finite and reviewer-reported; it does not prove universal identifiability or measured training gain. The owner must integrate the exact bytes, rerun native qualification, and perform fresh acceptance before any training admission.

