# Working notes: 09d287bbfa0b

## Review-ae7bce401b5111fe repair

The pinned baseline was version 2.1.0. Its summary was a useful lead, but all
claims were remeasured against the selected source. The before battery found:
missing canonical `RULE_HASH`, stale selected authority text, no exact canonical
profile in 60 default draws, missing executable semantic lesson hooks, and an
override contract with thousands of exact-control/provenance failures.

Version 3.0.0 uses two deterministic schedule profiles:

- `canonical_core` (even sample indices) cycles the four canonical
  height/width/total-palette profiles exactly.
- `teaching_mix` (odd indices) contains one deliberate same-orbit collision
  across quadrants, one off-color axis cell, and one partially clipped orbit.
  Remaining sources prefer fully visible orbits so the transformation changes
  at least 3% of every checked default grid instead of becoming visually
  negligible on large canvases.

The alternating schedule is deliberate. A production lesson uses three demos;
any three consecutive samples include a mixed witness. The downstream rotation
probe materializes four pairs and holds each one out once; any remaining three
also include a mixed witness. Task-local tests enumerate eight cyclic starts and
all four query positions rather than inferring this property from witness
frequency.

Exact overrides are constructively supported across every difficulty band:
`grid_h`/`grid_w` 7..18, `sep_color` 1..6, `n_pixels` 2..8, and textures
`plain`, `multi_quadrant`, `clip`, `axis_dot`, `mixed`. The generator records
scheduled values through the same keyed provenance channel used by exact draws,
and `observe_overrides` reconstructs each requested value from returned pixels.
No override combination is intentionally rejected.

Declared semantic rivals are: single-quadrant-only reflection, reflecting axis
cells as sources, preserving original source cells against overwrite, and
all-or-nothing clipping. The first three fit every canonical pair; the fourth
is already refuted by clipped canonical examples but remains in generated
lesson checks. Finite rival passes do not prove unique induction against every
possible program.

The selected training and augmented solution records were rebound from a stale
legacy source string to the already pinned canonical program. The canonical
program itself and rule hash were not changed.
## Current reviewer considerations

Source SHA-256: `f6e03fa672237f8bcf931e9e0b3307dae1cb749b14272a9c04033f3ca01a4a34`.

# Decisions for review-e5e91eb64fe8d5ed

Task: `09d287bbfa0b`
Selected generator version: `3.0.0`
Final generator SHA-256: `f6e03fa672237f8bcf931e9e0b3307dae1cb749b14272a9c04033f3ca01a4a34`
Canonical rule hash: `36baa035a1e3`; exact Racket SHA-256: `5ba270db6110a201c0a50caddb0bc3215680ace8e936c2fca3b67d31c1877fcd`

The prior v3 repair in `notes.md` was used only as a lead. The selected source was remeasured with a fresh before battery before any change.

## D1 — Preserve the v3 distribution and canonical rule; repair the measured API defect only

**Choice.** Keep the existing `canonical_core` / `teaching_mix` curriculum, five observable axes, semantic rivals, and canonical Racket program unchanged. Repair only the strict call-scalar contract exposed by the before battery.

**Rationale.** The selected source already passed 11 of 12 battery stages. Rule smoke, canonical ownership, profile support, semantic checks, overrides, Racket lint, and authority synchronization were green; only `defect_lint` failed. A broader distribution or rule rewrite would weaken causal attribution and risk regressions in an already measured repair.

**Alternatives rejected.** Bump the generator version and resample all valid outputs; modify the canonical Racket rule; rework the alternating curriculum; suppress strict-scalar warnings as harmless Python coercions.

**Probe/evidence.** `checks/before/checks/09d287bbfa0b_before_battery_summary.json` records 11/12 on source `2603fc26…`, with only `defect_lint` failed. `checks/after-final/checks/09d287bbfa0b_after_battery_summary.json` records 12/12 on the final source.

**Failure modes and limits.** The final green battery supports the declared domain and finite probes, not every possible generator call or alternative ARC hypothesis. The current deterministic schedule remains predictable by sample-index parity, as documented by the prior review.

## D2 — Reject malformed call scalars before constructing `GenCtx`

**Choice.** Require `type(seed) is int`, require `type(sample_index) is int and sample_index >= 0`, and restrict `difficulty` to `None`, `easy`, `medium`, or `hard`.

**Rationale.** The baseline silently treated invalid difficulty values as medium. After that first fix, a complete defect-lint pass exposed 33 additional accepted invalid values involving boolean, float, string, and negative call arguments. Python booleans alias integers and negative indexes alter the curriculum residue, so accepting them undermines replay identity and can admit unintended training examples.

**Alternatives rejected.** Coerce strings/floats to integers; permit booleans; permit negative indexes via modulo; validate only inside tests; rely on `gen_ctx` to reject values it currently accepts.

**Probe/evidence.** Failing-before and passing-after tests are retained in `checks/tdd-difficulty-red.log`, `checks/tdd-difficulty-green.log`, `checks/tdd-call-scalars-red.log`, and `checks/tdd-call-scalars-green.log`. The intermediate battery failure is retained under `checks/after/`; the final defect lint is green under `checks/after-final/`.

**Version decision.** `VERSION` remains `3.0.0` because every formerly valid call follows the same code path and produces the same grid; the change only rejects values outside the declared public contract. The generator SHA changed, and all evidence is bound to that final SHA.

**Failure modes and limits.** Very large positive Python integers remain allowed. That matches the declared integer contract; boundedness was not a measured requirement in this packet.

## D3 — Make task tests source-bound in both repository and portable layouts

**Choice.** Replace the task test’s manual generator loader with `reviewer_support.find_root(__file__)`, `load_selected_generator`, and `canonical_pairs`. Insert `shared/runtime` only in the repository layout, never when a selected `RUNTIME_MANIFEST.json` is present.

**Rationale.** Direct repository tests passed, but the first portable task-test snapshot mixed its selected runtime with a mirrored source runtime. The loader correctly rejected that cross-tree dependency cache, producing three failures unrelated to generator behavior.

**Alternatives rejected.** Disable the loader’s source-coherence check; import private `puzzle_generators.per_puzzle` aliases; hard-code parent depths; mark the portable stage blocked despite a task-local source-path bug.

**Probe/evidence.** The failed portable run is `checks/task-tests-final/`. The corrected selected-runtime run is `checks/task-tests-final-v2/`, whose JUnit receipt records 114 tests, 0 failures, 0 errors, and 0 skips. The direct focused run is `checks/focused-tests-portability-fix.log`.

**Failure modes and limits.** A single process still must not load generators from two different runtime trees. That is an intentional safety boundary, not a limitation to remove.

## D4 — Prototype one minimal rule parameter: source traversal order

**Choice.** Add a task-local, non-production `scan_order` prototype with settings `row_major` (canonical/default) and `reverse_row_major`. Hold background, axis detection, source eligibility, three non-identity reflections, clipping, and overwrite operation fixed. The default returns the exact canonical Racket bytes; the alternative changes one traversal fragment.

**Rationale.** Traversal order is a small compositional parameter of the existing reasoning pattern. It changes only collision resolution and does not invent new objects, colors, axes, or output operations. A visible same-orbit color conflict makes the setting inferable from examples.

**Alternatives rejected.** Parameterize background color or reflection geometry, which would alter object roles; add multiple parameters at once; edit the selected canonical rule; generate alternatives with a Python mirror instead of exact Racket execution.

**Probe/evidence.** `generators/09d287bbfa0b/workspace/parametric/prototype.py` and its README are covered by 22 focused tests. `checks/parametric/final-v2/private/report.json` binds the final generator, canonical replay, two rule hashes, two settings, two complete episodes, and a distinguishing witness.

**Failure modes and limits.** This is a proposed authoring prototype, not canonical or production approval. It is checked only against the declared two-setting rival on seeds 0 and 1, medium difficulty, start 0.

## D5 — Reject the clipped `mixed` witness and use one common fully visible collision domain

**Prior choice.** The first prototype attempted to use the generator’s `mixed` texture because it already contains a collision.

**New choice.** Use `texture="multi_quadrant"` and `n_pixels=8` for every parameter setting.

**Reason.** Exact Racket execution showed that the forced `mixed` collision is deliberately clipped and has no shared empty target on which row-major and reverse-row-major differ. The two settings therefore produced identical outputs, making the latent parameter unteachable. The replacement domain forces a fully visible, distinct-color same-orbit collision while keeping the input distribution identical across settings.

**Alternatives rejected.** Special-case labels after generation; use different textures for different settings, which would leak the parameter; accept episodes where only the hidden query distinguishes the settings; rely on source inspection rather than executed outputs.

**Probe/evidence.** The failed attempt is retained in `checks/parametric/tdd-episode-green.log`. The corrected RED/GREEN path is retained in `checks/parametric/tdd-episode-red.log` and `checks/parametric/tdd-episode-green-v2.log`; final evidence is under `checks/parametric/final-v2/`.

**Failure modes and limits.** The constrained prototype domain is intentionally narrower than the production generator. It demonstrates parameter teachability, not distribution breadth.

## D6 — Keep public challenges free of parameter and answer leakage

**Choice.** Select one parameter once per deterministic episode; expose only three labelled demonstrations and an unlabelled query in `public/`. Retain the setting, Racket source, rival predictions, and query answer only in `private/` evidence.

**Rationale.** A parameterized lesson is only useful if the learner infers the setting from demonstrations. Publishing the setting or query answer would turn the test into metadata lookup or direct leakage.

**Alternatives rejected.** Include `scan_order` as public metadata; expose both candidate outputs; vary the setting pair-by-pair; omit private evidence and make the authoring claim unreplayable.

**Probe/evidence.** `test_parametric_scan_order.py` checks episode-scoped determinism, public/private schema separation, token-level leakage, exact Racket replay, and rival refutation. `checks/parametric/final-v2/public/` and `private/` retain the resulting split.

**Failure modes and limits.** Token scanning catches direct serialized leakage, not every indirect statistical cue. Both settings deliberately use the same input constraints to reduce one obvious cue.

## D7 — Report finite lesson evidence without overstating induction

**Choice.** Run 100 production lessons per difficulty band, each with three demos and one query, then hold out each of the four materialized pairs once. Require rotation identifiability for this census.

**Rationale.** The task has canonical-fitting shortcuts, so the 12-lesson battery smoke test is insufficient by itself. Query rotation tests whether the teaching witness remains in the demonstrations rather than being accidentally placed only in the query.

**Alternatives rejected.** Report the 600-grid semantic census as lesson evidence; infer identifiability from witness frequency; test only production order; claim universal uniqueness after finite rival checks.

**Probe/evidence.** `checks/lesson-census-final.summary.json` records 300/300 lessons materialized, 1,200 unique pairs, 1,200 rotations, zero ambiguity, zero hook warnings, and zero scoring errors. Every declared rival was refuted in all 100 lessons of every band.

**Failure modes and limits.** This is a finite declared-rival census. It does not prove uniqueness against undeclared programs or all seeds, and no `LESSON_SCHEDULE_PERIOD` is declared for exhaustive period enumeration.

## D8 — Preserve negative evidence and keep audit targets unchanged

**Choice.** Retain the failed before/intermediate batteries, TDD RED logs, the failed first parametric setting, the first portable task-test failure, and the first visible solve failure. Audit targets `ef02aedbac38` and `641108b687a1` are documented but not edited.

**Rationale.** These artifacts prove what the final tests detect and distinguish task-local repairs from peer-review findings.

**Alternatives rejected.** Return only green summaries; rewrite the solve history; patch audit targets; delete the interrupted audit wrapper and report it as complete.

**Probe/evidence.** See `checks/before/`, `checks/after/`, `checks/parametric/tdd-episode-green.log`, `checks/task-tests-final/`, `checks/post-repair-solve-check-1.log`, and `AUDIT.md`.

**Failure modes and limits.** The return approaches the member budget, so `package_return.py` may bundle checks into its verified evidence archive. The full 11.5 MiB lesson census is retained because it is the source-bound replay artifact behind the compact summary.

## Self-review for new shortcuts or restrictions

The canonical repair adds no input restriction for valid calls and does not alter generated grids, the schedule, or the Racket rule; it only rejects malformed API scalars. The parametric prototype intentionally narrows its own non-production input domain to one fully visible collision class, and that limitation is explicit rather than being presented as production diversity.
