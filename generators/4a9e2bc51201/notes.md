# Working notes: 4a9e2bc51201

## 2026-10-04 repair review

Baseline generator SHA-256: `f9f3f767b4b9cd578cd5907e4bec4f46898e858c398dcf6d40687dd64d891447`.
Final generator SHA-256: `c60c1054ff9e9ae881c5bd268aa2bd84ceed5d56a5aac625d7fee24e30785a6d`.
Canonical rule hash: `88c9535f3ba5` (unchanged).

### Root cause

The selected rule reflects a colored cell only into an empty mirror target.
Occupied mirror partners are legal and preserved, including differently colored
partners. The baseline sampler generated only empty-target cases, and its
`self_check` incorrectly elevated that sampling choice into an invariant. It
therefore rejected canonical lawful inputs and never taught the occupied-target
branch. Several advertised palette/texture/density controls were aliases, dead,
or ignored; the canonical rule hash was not pinned.

### Repair

- Replaced independent-cell rejection sampling with constructive row/distance
  reflection orbits around one full-height color-5 guide.
- Ordinary draws include open sources on both sides and an occupied pair; with
  at least two colors, one occupied pair is deliberately conflicting.
- Reduced controls to seven exact observable axes and added strict unknown/type/
  range validation plus `observe_overrides`.
- Added a deterministic canonical-profile anchor every fourth unoverridden draw,
  with difficulty-aware expanded samples otherwise.
- Added executable witnesses and rivals for left-only, right-only, and overwrite-
  occupied shortcuts, plus a three-example lesson-identifiability contract.
- Rewrote `self_check` around the lawful domain rather than the sampler template.
- Added 49 focused tests and `workspace/reflection_audit.py` for independent replay.

### Evidence

The completed after battery is 12/12 green at the final generator hash. Portable
task tests pass 49/49. The production lesson census materialized 100 lessons per
band and checked all 1,200 query rotations with zero ambiguity/errors and 1,200
unique inputs. The task-local probe checked 100 draws per band plus 12 lesson
windows per band; every sample refuted all three declared rivals.

Finite rivals and finite sampling do not prove universal identifiability. The
selected Racket program remains the label authority.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c60c1054ff9e9ae881c5bd268aa2bd84ceed5d56a5aac625d7fee24e30785a6d`.

# Decisions for 4a9e2bc51201

Final generator: version `2.0.0`, SHA-256 `c60c1054ff9e9ae881c5bd268aa2bd84ceed5d56a5aac625d7fee24e30785a6d`.

## D1 — Preserve the canonical Racket authority

**Input choice.** Change the Python sampler, validator, semantic contract, and tests; do not change the selected Racket rule or canonical records.

**Original rationale.** The baseline docstring already described “copy at the mirror position only if that position is empty.” Rule smoke passed before repair, and direct inspection showed the canonical authority correctly handles both empty and occupied mirror targets. No evidence justified a rule change.

**Alternatives considered.** Restrict the rule to the baseline’s empty-target-only domain; overwrite occupied partners; or edit canonical records to match the sampler. All would reverse authority: they would change a correct task to preserve a defective distribution.

**Probes.** Canonical input/output parity, real-Racket rule smoke, and authority synchronization. The final battery passed both authority stages with rule hash `88c9535f3ba5`.

**Failure modes and limits.** Python oracle code is supplementary and could drift, so final labels continue to come from Racket. The authority was tested on canonical and generated inputs, not formally verified for arbitrary malformed grids.

## D2 — Model inputs as reflection orbits

**Input choice.** Select row/distance orbits around a unique vertical color-5 guide, then assign each orbit as one-sided or already occupied on both sides.

**Original rationale.** Unknown beyond the baseline source. The prior implementation sampled cells independently and then required every mirror target to be empty; that made its sampling convenience look like a task law.

**Alternatives considered.** Continue rejection sampling random cells; post-edit random grids until all desired cases appear; or generate arbitrary grids and depend on `self_check`. Orbit construction is simpler, guarantees capacity before placement, and makes the semantic branches explicit.

**Probes.** Exact counts recovered by `observe_overrides`, deterministic replay, no duplicate orbit use, no out-of-bounds mirror positions, and 49 focused tests.

**Failure modes and limits.** Orbit construction intentionally excludes marks whose mirror falls outside the grid. That matches the selected lawful domain but does not attempt to characterize how the Racket rule behaves on every malformed input.

## D3 — Include both open-source directions and occupied targets in ordinary samples

**Input choice.** Default `open_side="mixed"`, at least four open orbits, and one to three occupied orbits. When at least two colors are available, the first occupied pair is forced to use different colors.

**Original rationale.** The baseline summary only said marks were asymmetric. Its code permitted either side by chance but supplied no guaranteed bidirectional witness and expressly forbade occupied targets.

**Alternatives considered.** Randomly hope each lesson contains all branches; put branch cases only in rare hard samples; or rely on multi-example lessons to combine weak examples. All permit long stretches of data fitting one-way or overwrite shortcuts.

**Probes.** `SEMANTIC_WITNESSES`, three rivals, `lesson_identifiable`, the 300-lesson census, and the 300-draw replay probe. Every ordinary replay draw disagreed with all three rivals.

**Failure modes and limits.** Strong per-example counterfactuals may make the intended rule easier than some natural ARC instances. This is deliberate for SFT data quality; geometric and palette variability remain broad enough to avoid a single visual template.

## D4 — Replace decorative controls with seven exact observable axes

**Input choice.** Keep only `grid_h`, `grid_w`, `divider_bias`, `n_open_pairs`, `n_occupied_pairs`, `open_side`, and `n_distinct_colors`.

**Original rationale.** The baseline advertised `palette_kind`, `palette_size`, `n_distinct_colors`, `density`, `texture`, and `position_bias`, but generation used one fixed palette, ignored several controls, and made `texture` an alias or a path to invalid degenerates.

**Alternatives considered.** Implement all legacy names, keep aliases for compatibility, or mark dead controls incompatible. The legacy names described no distinct training semantics and would preserve ambiguity, so they were removed rather than simulated.

**Probes.** Boundary-value override tests for every axis, round-trip observation, unknown-key rejection, malformed-type rejection, and the repository override gate.

**Failure modes and limits.** This is an interface change from version 1.1.2. The assignment repairs an unapproved generator, so exactness was favored over compatibility with decorative overrides that never worked as declared.

## D5 — Use strict override typing

**Input choice.** Require actual `int` values for integer axes and actual declared strings for choices; reject booleans, floats, numeric strings, unknown keys, and out-of-range values.

**Original rationale.** Unknown. The shared draw helper can coerce some values, so a task-local pre-validation layer was necessary to make the public contract honest.

**Alternatives considered.** Coerce friendly values or silently clamp ranges. Both can hide upstream dataset bugs and make replay metadata lie about what was requested.

**Probes.** Focused malformed-control tests and the final override gate (`unknown_key_verdict: rejected`).

**Failure modes and limits.** Strict typing is less permissive for interactive callers, but generator control metadata is a reproducibility contract rather than a UI form.

## D6 — Anchor canonical profiles deterministically

**Input choice.** Every fourth unoverridden sample cycles through four canonical `(height, width, distinct-color-count)` profiles; remaining samples use difficulty-aware expanded ranges.

**Original rationale.** The baseline used narrow difficulty ranges but no explicit canonical schedule. The profile-floor requirement exposed that accidental shape/palette overlap is not reliable support.

**Alternatives considered.** Increase random probability of canonical profiles; force every sample to canonical dimensions; or maintain separate canonical-only difficulty bands. A deterministic one-in-four anchor is replayable and guarantees floor coverage while leaving 75% of the schedule for expansion.

**Probes.** `schedule_profile`, repository profile floor, exact-profile counts in `reflection_audit.py`, and schedule profile counts.

**Failure modes and limits.** The schedule is periodic and therefore learnable from sample index metadata if such metadata were exposed to a model. The training grid itself contains no schedule marker, and production sampling hashes seeds/starts independently.

## D7 — Separate difficulty through range, not through missing semantics

**Input choice.** Easy/medium/hard vary grid size, number of open and occupied orbits, and palette cardinality, while every band retains all decisive semantic branches.

**Original rationale.** The baseline varied dimensions and mark count by difficulty but did not define a semantic curriculum.

**Alternatives considered.** Make easy examples one-directional or omit occupied targets, adding them only later. That would train an incorrect simpler rule in an entire band.

**Probes.** Per-band exact controls, 100 lessons per band, 100 replay draws per band, and all cyclic residues in the production census.

**Failure modes and limits.** Difficulty is heuristic rather than model-calibrated. More cells and colors may not correlate monotonically with Qwen3.5-9B error rate; no model evaluation was run here.

## D8 — Pin a finite semantic rival set

**Input choice.** Declare and execute `left_to_right_only`, `right_to_left_only`, and `overwrite_occupied_targets` as both sample-level rivals and lesson competitors.

**Original rationale.** None existed in the baseline. These are the smallest plausible alternatives induced directly by its missing rule branches.

**Alternatives considered.** Add many generic transformations or claim uniqueness from witness frequency alone. A compact, task-derived rival set is executable and interpretable; generic enumeration would be expensive and still incomplete.

**Probes.** Canonical rival fit, sample disagreement, lesson-level refutation, all query rotations, and 12 additional consecutive windows per band.

**Failure modes and limits.** Passing a finite rival set is not a proof of unique induction. Undeclared conditional, object-level, or memorization rules may still fit finite lessons.

## D9 — Make `self_check` describe legality, not one generator template

**Input choice.** Require a rectangular ARC grid, exactly one full-height 5 guide and no extra 5s, all colored marks mirrorable in bounds, and at least one open orbit so the rule changes the input. Accept occupied mirror pairs, including conflicting colors.

**Original rationale.** The baseline validator mirrored its own empty-target placement strategy and required at least three marks, which rejected canonical legal inputs.

**Alternatives considered.** Accept every rectangular grid containing a 5-column, or require all ordinary sampling witnesses in every override case. The former is too loose; the latter would make valid explicit controls such as `n_occupied_pairs=0` impossible.

**Probes.** All canonical pairs, invalid guide variants, extra color-5 cells, out-of-bounds cases, identity-only grids, and generated samples across bands and override boundaries.

**Failure modes and limits.** The validator deliberately rejects identity cases even though the Racket rule can execute them; they are poor training examples. This is a curriculum admissibility decision, not a claim that Racket execution is undefined.

## D10 — Add a task-local independent replay probe

**Input choice.** Add `workspace/reflection_audit.py`, which discovers the live generator’s rival declarations, independently transcribes the rule, checks canonical acceptance/parity, samples each band, and tests production-style lesson windows.

**Original rationale.** The workspace contained only a placeholder README. Reconstructing the semantic analysis by hand would be error-prone for later reviewers.

**Alternatives considered.** Put the probe into shared tooling or rely only on pytest. Shared-tool changes are outside this task delta; pytest proves fixed cases but does not provide a compact distribution report.

**Probes.** The tool itself is covered by a focused regression test. Its final 100-per-band report is `checks/reflection-audit.json`.

**Failure modes and limits.** The independent Python oracle is still a transcription and finite sampling is not exhaustive. The report says so and retains Racket as authority.
