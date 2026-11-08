# Working notes: 27f5eba1051c

## Review 2026-10-03 — generator 5.0.0

The retained associated note in `evidence/associated_notes.jsonl` was used only as a lead. It described the previous exact-profile sampler, but all baseline claims were remeasured against the selected source.

### Baseline finding

Version 4.0.0 preserved five linked public signatures and passed the structural battery, but it did not expose an executable semantic contract. More importantly, the canonical pairs admit at least four materially different rules: bounding-box area instead of occupied-cell count, row before column in ties, color before column in ties, and treating disconnected same-color cells as one object. The original generator also made all three object colors distinct and did not guarantee a cell-count/bounding-box conflict, so those shortcuts could survive generated lessons. The portable task tests additionally guessed a repository-relative canonical-data path and failed in the copied task-test runtime.

### Repair

- Added a deterministic four-slot semantic schedule: `canonical_linked`, `column_tie`, `color_tie`, `semantic_stress`.
- Made the tie profiles answer-bearing for the secondary ordering keys.
- Added lawful repeated colors across separated components.
- Added a stress profile with object sizes 7/6/5 where the largest and smallest both occupy 3x3 bounding boxes, the smallest is leftmost, the largest and smallest share a color, and the selected crop contains interior zeros.
- Added `strict_canonical_like`, eight executable rivals, nine witnesses, witness/rival claims, a lesson identifiability hook, and four `CANONICAL_SHORTCUTS` proven to fit all five usable canonical pairs.
- Added regression tests that require all four schedule roles, verify the stress counterexamples, and require every cyclic four-example window to refute every declared lesson competitor.
- Replaced repository-relative canonical-data test paths with `reviewer_support` portable helpers.
- Extended `workspace/probe_candidate_rivals.py` to consume the generator declarations directly, verify canonical shortcut fit, and test every cyclic schedule residue.

### Final measured evidence

- Generator SHA-256: `7c11190c553e9591778e3b6a52e121eea074881c44511c70291dc11395c35bc4`.
- Task tests: 32 passed and 772 subtests passed (`checks/task-tests/result.json`).
- Candidate-rival probe: all four declared shortcuts fit 5/5 canonical pairs; every one of eight rivals was refuted in all 200 four-example windows per band and all four schedule starts (`checks/candidate-rivals-final.log`).
- Lesson census: 100/100 lessons materialized per band, zero ambiguity, zero scoring errors, 500/500 unique inputs per band; every declared rival and canonical shortcut was refuted in every lesson (`checks/lesson-census-final.json`).
- Post-repair visible-only solve: one attempt, 4/4 visible examples, earlier rule exposure declared yes, reference consultation during solve declared no (`solve/summary.json`).

### Limits

The rival set is finite and hand-authored; passing it is not a proof of universal identifiability. The shared census samples production lessons but does not rotate each individual pair through the query role; the task-local cyclic-window probe covers all four deterministic schedule starts. Exact public-linked profiles remain intentionally prominent because the goal is faithful task-family training rather than unrestricted object-selection scenes.
## Current reviewer considerations

Source SHA-256: `7c11190c553e9591778e3b6a52e121eea074881c44511c70291dc11395c35bc4`.

# Decisions for 27f5eba1051c

## D1 — Keep the canonical Racket authority unchanged

**Choice.** Change only the Python generator, task-local tests, workspace probe, summary, and notes. Keep the canonical row and Racket program unchanged.

**Rationale.** Rule smoke and all five canonical train/test pairs supported the existing authority: clear the rank marker, find monochrome 4-connected objects, sort by occupied-cell count descending then leftmost column then color, and crop the selected bounding box. The defect was teaching coverage, not execution.

**Alternatives considered.** Rewriting the Racket rule for readability or adding explicit input guards. Rejected because it would add authority risk without changing the intended transform.

**Probe.** Final rule smoke, Racket lint, and authority sync are green in `checks/after-final/result.json`.

**Failure mode / limit.** The Racket rule is defined outside the generator's strict domain; on malformed overlapping scenes it may still produce a grid. That is appropriate for this repair because strict-domain validation belongs to the generator.

## D2 — Use a deterministic four-slot lesson schedule

**Choice.** Set `EXAMPLES_NEEDED = 4` and cycle by `sample_index % 4` through `canonical_linked`, `column_tie`, `color_tie`, and `semantic_stress`.

**Original rationale.** Unknown; v4 selected among exact/generalized profiles probabilistically and did not guarantee semantic coverage inside a complete lesson.

**Rationale for repair.** A lesson-level guarantee is stronger and cheaper to verify than marginal witness frequency. Four examples are enough to preserve a public-linked form while dedicating one example to each ordering tie and one to multiple shortcut conflicts.

**Alternatives considered.** Random weighted sampling, six-example schedules, or one monolithic adversarial scene. Random weighting cannot guarantee a witness per lesson; six examples increase training cost; one monolithic scene is harder to interpret and can create accidental coupled shortcuts.

**Probes.** Task tests enumerate every cyclic four-example start. `workspace/probe_candidate_rivals.py` checks 200 windows per band with 50 starts from each residue (`checks/candidate-rivals-final.log`).

**Failure mode / limit.** A deterministic schedule creates a learnable periodic role order. The layouts, palettes, ranks, and linked-profile choice still vary by seed, but future sampling systems that expose raw sequence position should consider shuffling complete lessons after materialization.

## D3 — Preserve canonical-linked morphology in one schedule slot

**Choice.** Retain the five recovered public signatures, including the rank/object color-alias case and the held-out equal-area signature, and draw among them in the `canonical_linked` slot.

**Original rationale.** The associated prior note said the exact profiles were recovered from public canvas sizes, D4-normalized masks, ranks, equal-area relations, and color aliasing. This was treated as a lead and remeasured.

**Rationale for repair.** Semantic stress alone would broaden the domain but could drift from the visual family. Keeping one linked slot anchors each lesson to canonical morphology and preserves profile-floor support.

**Alternatives considered.** Remove exact profiles and rely entirely on generalized polyominoes, or make all four examples exact public variants. The first risks family drift; the second leaves known shortcuts intact.

**Probe.** Exact-signature tests cover placement and palette variation; final profile floor reports 24/60 exact-profile and 25/60 canonical-envelope hits (`checks/after-final/checks/27f5eba1051c_after_profile_floor.log`).

**Failure mode / limit.** Exact profiles are intentionally overrepresented relative to an unconstrained object-cropping universe. This is a task-family generator, not a generic curriculum for all ranked-object scenes.

## D4 — Make the column and color tie-breakers independently answer-bearing

**Choice.** Use separate `column_tie` and `color_tie` constructors. The column profile holds area equal and makes the leftmost tied object the selected answer; the color profile holds both area and leftmost column equal and makes lower color the selected answer.

**Original rationale.** v4 tracked tie features but did not guarantee the relevant secondary key changed the selected output in every lesson.

**Rationale for repair.** Merely containing a tie is not teaching evidence if both candidate outputs are identical or the query rank selects another object.

**Alternatives considered.** A single profile with a three-way tie. Rejected because it entangles row/column/color differences and makes the decisive key harder to audit.

**Probes.** `test_column_profile_makes_column_key_answer_bearing` and `test_color_profile_makes_color_key_answer_bearing`; semantic witnesses `column_precedes_color_on_size_tie`, `column_precedes_row_on_size_tie`, and `color_breaks_same_column_tie`.

**Failure mode / limit.** The color tie uses monochrome components with equal left columns, a narrow but legal construction. It proves the ordering key but does not exhaust all geometric tie arrangements.

## D5 — Permit repeated colors across disconnected objects

**Choice.** Broaden the lawful grammar so two separated 4-connected objects may share a color; object identity remains connected-component identity.

**Original rationale.** v4 sampled distinct colors, likely for visual clarity and easy separation.

**Rationale for repair.** All five canonical pairs also use distinct object colors, so a per-color grouping rule fits them. A repeated-color scene is the minimal counterexample that distinguishes connected objects from color classes.

**Alternatives considered.** Keep distinct colors and declare color grouping out of domain. Rejected because the canonical Racket authority uses `objects`, not color groups, and the expanded domain is easy to validate without ambiguity.

**Probe.** Stress scenes fire `disconnected_same_color_are_separate`; the `group_same_color` rival fits 5/5 canonical pairs but is refuted in every final lesson.

**Failure mode / limit.** Same-color objects are always spatially separated in the generated domain. Touching same-color regions would be one object by the canonical connectivity definition and remain out of scope.

## D6 — Use a 7/6/5 occupied-cell stress profile with a 3x3 bbox conflict

**Choice.** Construct three objects with occupied-cell counts 7, 6, and 5. The largest and smallest each have a 3x3 bounding box; the smallest is leftmost; largest and smallest share a color; the largest crop contains internal zeros.

**Original rationale.** No equivalent stress profile existed in v4.

**Rationale for repair.** One legal scene simultaneously refutes bounding-box area, ascending area, left-to-right selection, same-color merging, and solid-bbox filling while retaining a clear canonical answer.

**Alternatives considered.** Randomly search until all conflicts occur or create one profile per rival. Constructive generation is deterministic and avoids rejection tails; one profile per rival would require more examples per lesson.

**Probe.** Dedicated tests compare canonical output to each rival. The final semantic gate observed the stress witnesses 157/600 times and verified each corresponding rival claim 60/60 times.

**Failure mode / limit.** Reusing a fixed size pattern could itself become a role cue. Shapes, placements, palettes, rank-linked slot selection, and canvas sizes vary; nevertheless, future revisions could diversify the stress size triples while preserving the same conflict certificate.

## D7 — Declare canonical-fitting shortcuts separately from general rivals

**Choice.** Add `CANONICAL_SHORTCUTS` for `bbox_area`, `row_before_column_ties`, `color_before_column_ties`, and `group_same_color`, while keeping eight rules in `LESSON_COMPETITORS` / `SEMANTIC_RIVALS`.

**Rationale.** A shortcut should not be called canonical-ambiguous unless it is first shown to fit every usable canonical pair. Separating the declarations lets the shared gate verify that claim and then demand generated counterexamples.

**Alternatives considered.** Put all rivals in one list or hard-code names in the workspace probe. A single list blurs canonical ambiguity with ordinary negatives; copied names drift from source.

**Probe.** `test_declared_canonical_shortcuts_fit_every_public_pair`; declaration-driven output in `checks/candidate-rivals-final.log`.

**Failure mode / limit.** The list is hand-authored and cannot cover arbitrary synthesized programs. The question answer proposes a shared survivorship gate as the next step.

## D8 — Use portable canonical-data helpers in tests

**Choice.** Replace guessed filesystem roots with `reviewer_support.canonical_pairs`, `canonical_path`, and `find_root`.

**Original rationale.** The prior tests assumed the source repository layout.

**Rationale for repair.** The required `task_tests` stage copies tests into an isolated runtime; repository-relative guesses are invalid there. The supplied helper is source-bound and records the canonical authority copied into the runtime.

**Alternatives considered.** Copy the canonical JSONL into the task directory or walk parents until a matching filename is found. The first duplicates authority; the second is brittle and can bind the wrong file.

**Probe.** Baseline: 2 failures / 26 tests (`checks/task-tests-before/result.json`). Final: 32 tests and 772 subtests pass (`checks/task-tests-final/result.json`).

**Failure mode / limit.** These helpers expose canonical answers and must remain closed during visible-only solve episodes; the solve records followed that restriction.

## D9 — Keep the reusable rival probe task-local and declaration-driven

**Choice.** Extend `workspace/probe_candidate_rivals.py` rather than create a shared dependency.

**Rationale.** It is useful immediately for this task and safe to return with the allowed delta. It loads the live generator declarations, checks canonical fit, covers all cyclic starts, and reports unique-input counts.

**Alternatives considered.** Patch the shared semantic gate. Rejected in this assignment because shared source is outside the allowed change scope; the same idea is submitted as feedback and as the Qwen data-quality gate proposal.

**Probe.** `checks/candidate-rivals-final.log`.

**Failure mode / limit.** The probe is task-specific Python and does not synthesize new rivals. It is a reliable replay tool, not a general induction verifier.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/27f5eba1051c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
