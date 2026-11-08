# Working notes: 4a279b104523

## Review 2026-10-04 — assignment review-2ce17f63785d081d

### Prior leads used

The selected baseline was measured directly; prior claims were not treated as current evidence. The assignment index row in `repo/shared/data/derived/kimi_generator_assignment.jsonl` was used only as a lead. It identified a missing `RULE_HASH` and historical `grid_h`/`grid_w` axis-honesty findings. The task-local `evidence/associated_notes.jsonl` was empty, so no prior return was imported as proof.

### Baseline findings

- Baseline generator SHA-256: `30240d65792e4f167a6eab4892d3c3a9d3f2f8f5de92d0f373faf64131e01346`, version `1.2.1`.
- It had no pinned `RULE_HASH`.
- `self_check` rejected the second canonical input because it assumed every source was above the color-8 axis.
- The sampler taught only above-to-below copying, while the canonical authority is bidirectional and clips out-of-bounds copies.
- Several advertised controls were ignored or dead; exact override behavior was not falsifiable.

### Selected design

Version `2.1.0` exposes only four observable controls: `grid_h`, `grid_w`, `n_cells`, and `source_side`. Unknown, mistyped, coerced, and out-of-range overrides raise. The generator samples one side of each reflection orbit, keeps the opposite target empty, and validates that rendered axes equal keyed draws.

The input grammar and curriculum are intentionally separate:

- `self_check` accepts lawful canonical inputs, including a canonical source whose reflected row is out of bounds.
- `strict_canonical_like` additionally requires empty in-bounds mirror targets for generated teaching examples.
- `rule_mirror` is a diagnostic Python mirror only; the selected Racket rule remains the authority.

Two executable rivals are retained: `above_only` and `grid_center`. The initial random distribution passed the small semantic smoke gate but failed a 300-lesson census in 10 lessons. The final three-slot schedule cycles `above`, `below`, `both`; its axis schedule cycles `center`, `offcenter`, `offcenter`. Every consecutive three-sample window therefore contains a below-source witness and an off-center-axis witness.

### Measured final evidence

Final generator SHA-256: `5d11dec78c4996ecc4b5184c34388755ae63f0e5e72d4df54abb013bd77e9505`.

- Completed after battery: 12/12 stages green (`checks/after-complete/`).
- Portable selected task tests: 81/81 passed (`checks/task-tests-final/`).
- Lesson census: 300/300 lessons, 1,200/1,200 unique inputs, zero ambiguity/warnings/errors; each rival refuted in 100/100 lessons per band (`checks/lesson-census-final.json`).
- Independent probe: 750 deterministic draws, zero self-check failures, 27/27 Racket parity checks (`checks/final/reference_probe-v2.json`).

Finite declared-rival testing is not a proof of universal identifiability. New observed shortcuts should be added as executable rivals before changing the schedule.
## Current reviewer considerations

Source SHA-256: `5d11dec78c4996ecc4b5184c34388755ae63f0e5e72d4df54abb013bd77e9505`.

# Decisions for 4a279b104523

This file records the final distribution and contract choices for generator SHA `5d11dec78c4996ecc4b5184c34388755ae63f0e5e72d4df54abb013bd77e9505`. “Original rationale” means rationale recoverable from the 1.2.1 source or retained notes; where none was recorded, it is marked unknown rather than reconstructed after the fact.

## D1 — Use the bidirectional color-8 row rule

**Decision.** Treat every nonzero/non-8 cell on either side of the unique full color-8 row as a source. Preserve each source and copy its color to `(2 * axis - row, column)` when that position is in bounds.

**Original rationale.** The 1.2.1 docstring and summary explicitly chose an above-to-below-only formulation. No rationale was recorded for narrowing the selected authority that way; the comments merely asserted that three above-source examples pinned the rule.

**Alternatives rejected.** Keep the one-way rule; reject below-axis inputs as degenerates; alter the Racket authority to match the generator. All three were rejected because an official canonical pair has below-axis sources and the selected Racket program already handles sources symmetrically.

**Probe/evidence.** G1 in `REVIEW.md`; canonical acceptance and geometry tests in `tests/test_generator.py`; baseline rejection in `checks/before_distribution_probe.json`; 27-input parity in `checks/final/reference_probe-v2.json`.

**Failure modes and limits.** A grid with multiple full 8 rows remains invalid because the axis is ambiguous. Sources with out-of-bounds mirror rows are lawful for canonical validation but are not sampled by the teaching generator. This distinction is tested explicitly.

## D2 — Preserve sources and clip only out-of-bounds copies

**Decision.** The diagnostic mirror starts from a copy of the input. It writes an opposite-side copy only when the reflected row is inside the canvas.

**Original rationale.** Unknown in the baseline generator, which only sampled in-bounds targets and therefore never expressed the clipping question.

**Alternatives rejected.** Delete sources after moving them; reject the canonical clipped source; resize the grid; wrap the copy. These contradict the official output or introduce an unobserved operation.

**Probe/evidence.** `test_canonical_out_of_bounds_reflection_is_clipped_not_rejected`; Racket rule smoke and authority sync in `checks/after-complete/`.

**Failure modes and limits.** A pre-existing same-color mirror partner is lawful but not strict-teaching-like; a different-color partner is rejected as a conflict because overwrite semantics would be ambiguous from the input alone.

## D3 — Replace nine nominal axes with four observable axes

**Decision.** Public axes are only `grid_h`, `grid_w`, `n_cells`, and `source_side`.

**Original rationale.** The baseline claimed “combinatorial axes (8)” while listing nine names. `palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density`, and `texture` were aliases, constants, degenerate selectors, or ignored values. No evidence showed that they were independently controllable.

**Alternatives rejected.** Preserve every old key for compatibility; implement all old keys as new independent controls; leave ignored controls documented as advisory. Retaining fake axes is worse than an explicit contract break for a not-yet-approved generator. Implementing them would enlarge the state space without task-specific teaching value.

**Probe/evidence.** G2/G4; baseline override reproductions in `checks/before_distribution_probe.json`; final exhaustive matrix in `checks/after-complete/checks/4a279b104523_after_override_results.json`.

**Failure modes and limits.** Downstream callers using obsolete keys now receive a clear `ValueError`. That is intentional: silent acceptance previously produced mislabeled curriculum requests.

## D4 — Enforce exact override types, ranges, and unknown-key rejection

**Decision.** Integer axes reject booleans and non-integers; all values must fall in the declared public domain; `source_side` must be one of three exact strings; every unknown key is rejected before RNG use.

**Original rationale.** None was recorded for the baseline’s permissive `**overrides`. The generation context only validated keys that happened to be consumed, so typos and dead axes passed silently.

**Alternatives rejected.** Coerce strings/floats to integers; ignore unknown keys; use difficulty-specific public ranges. Coercion hides data-pipeline mistakes, ignored keys are non-falsifiable, and difficulty-local rejection contradicts a single advertised axis domain.

**Probe/evidence.** Parameterized invalid/coercion tests; 28,080 strict accepted combinations and unknown-key rejection in the final override report.

**Failure modes and limits.** The four domains were chosen so every joint combination is feasible, therefore `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty. If a future axis creates incompatibilities, they must be declared rather than accepted under a legacy policy.

## D5 — Height domain 5–14 with canonical-scale weighting

**Decision.** `grid_h` is exactly controllable over 5–14. Unoverridden sampling keeps every value live but weights canonical heights 5, 6, and 7; hard also gives additional weight to 10–14.

**Original rationale.** Baseline metadata already advertised 5–14, but easy generation actually used 7–9, medium 8–11, and hard 11–14, so canonical heights were absent or rare. No rationale for those mismatched ranges was recorded.

**Alternatives rejected.** Restrict all generation to canonical heights; use a uniform 5–14 draw; retain disjoint difficulty bands. Canonical-only would overfit shape, uniform sampling failed the profile-floor intent, and disjoint bands made legal overrides reject unexpectedly.

**Probe/evidence.** Profile-floor exact hits easy 2/20, medium 4/20, hard 1/20 in `checks/after-complete/checks/4a279b104523_after_profile_floor.json`; 37/52/52 distinct shapes by band in the independent probe.

**Failure modes and limits.** Off-center schedule slots omit unoverridden height 5 because that height can force the center axis for high `n_cells`; an explicit `grid_h=5` override remains legal and takes the only feasible axis. Thus the exact override wins over the teaching preference.

## D6 — Width domain 4–11 with canonical-scale weighting

**Decision.** `grid_w` is exactly controllable over 4–11. Canonical widths 5 and 6 are weighted in all bands, while larger widths receive extra hard/medium support.

**Original rationale.** Baseline metadata advertised 4–11, but default ranges were easy 5–7, medium 6–9, hard 8–11. No rationale was recorded for excluding legal endpoints by difficulty.

**Alternatives rejected.** Canonical-only widths; uniform width; difficulty-local override ranges. The chosen mixture keeps profile support without collapsing geometric diversity.

**Probe/evidence.** Final profile-floor report, strict override matrix, and independent distinct-shape/profile counts.

**Failure modes and limits.** Width affects the number of available reflection orbits. The minimum width 4 remains jointly feasible with maximum `n_cells=8` because height/axis feasibility is checked before placement.

## D7 — Source count domain 2–8, difficulty-weighted

**Decision.** Generate exactly 2–8 source cells. Easy weights 2–4, medium 3–6, and hard 5–8 while retaining the entire domain in every band.

**Original rationale.** The baseline invariant required at least two sources to refute “mirror one cell,” and metadata advertised 1–8. Actual generation ignored `n_cells` and could produce 9 sources in the retained hard probe. No rationale supported allowing one or exceeding eight.

**Alternatives rejected.** Permit one source; keep an unbounded axis-dependent count; use a fixed count. One source weakens teaching, unbounded counts violate the contract, and fixed counts create a visual shortcut.

**Probe/evidence.** Exact overrides across all boundaries; `observe_overrides`; source-orbit uniqueness and mirror-target tests.

**Failure modes and limits.** `n_cells` counts source cells, not output additions. A mixed-side example with two cells is forced to contain one source on each side.

## D8 — Three-slot source-side teaching schedule

**Decision.** For unoverridden generation, `sample_index mod 3` chooses `above`, `below`, then `both`. An explicit `source_side` override supersedes the schedule.

**Original rationale.** Baseline hard-coded above sources to keep mirrored additions visible. That was a useful visibility goal but accidentally taught a one-way rule.

**Alternatives rejected.** Independent random side per pair; all mixed examples; below-only addition; schedule based on seed. Independent random draws passed pair-level witness rates but produced ambiguous three-demo windows. All mixed examples are less diverse and make the profile less transparent. A sample-index schedule aligns with production lesson windows and is replayable.

**Probe/evidence.** G3; intermediate 10/300 ambiguity in `checks/lesson-census.json`; final 0/300 in `checks/lesson-census-final.json`; all cyclic starts in `test_every_three_demo_schedule_refutes_declared_rivals`.

**Failure modes and limits.** The schedule is deliberately predictable. Its purpose is curriculum coverage, not cryptographic randomness. Other geometry, colors, orbits, and counts remain keyed.

## D9 — Center/off-center/off-center axis schedule

**Decision.** In each three-slot cycle, request a centered axis once and an off-center axis twice. If a requested mode is impossible under an exact legal override, use any feasible axis rather than reject the override.

**Original rationale.** Baseline comments recognized `grid_center` as a rival but did not implement a lesson-level guarantee that an off-center axis appears.

**Alternatives rejected.** Always off-center; random feasible axis; reject exact override combinations that cannot satisfy the schedule. Always off-center discards a natural case; random placement caused a census ambiguity; rejecting a legal shape to preserve a soft schedule reverses override precedence.

**Probe/evidence.** Final independent probe records off-center counts 190/250, 196/250, and 195/250 by band. The final census refutes `grid_center` in 100/100 lessons per band.

**Failure modes and limits.** Exact `grid_h=5` plus some counts may force a centered axis in an off-center slot. The three-slot source schedule still refutes `above_only`; an exact caller can construct multiple forced-center examples, so identifiability is a lesson-assembly responsibility when overriding every pair.

## D10 — Sample unique reflection orbits and keep mirror targets empty

**Decision.** Sample `(depth, column)` orbits without replacement, then choose one orientation per orbit. This guarantees no generated source occupies another source’s target and every output visibly adds a copy.

**Original rationale.** The baseline also attempted to keep targets empty by sampling only above the axis. The orbit formulation preserves the good visibility intent without imposing directionality.

**Alternatives rejected.** Sample arbitrary cells and retry collisions; allow prefilled same-color pairs; allow conflicting colors and define overwrite order. Unique orbits are simpler, deterministic, and remove silent non-teaching examples.

**Probe/evidence.** `test_generated_sources_have_empty_mirror_targets`; strict-canonical rate 600/600; zero generator crashes in the semantic gate.

**Failure modes and limits.** This is a strict training subset, not the full validator grammar. Same-color paired sources are lawful but omitted because they produce no visible change for that orbit.

## D11 — Content colors: ordinary ARC colors, one to four distinct, weighted to two

**Decision.** Sources use colors `(1,2,3,4,5,6,7,9)`. Choose one to four distinct colors, force each selected color to occur, and weight two colors most heavily.

**Original rationale.** Baseline sampled the same ordinary colors but had no real palette controls. Canonical examples all use two content colors, which motivated the final weighting; no original rationale was documented.

**Alternatives rejected.** Fixed two-color palette; all eight colors; expose palette size as another public axis. Fixed two is shortcut-prone, all eight is visually noisy and impossible at low `n_cells`, and an extra axis adds little semantic value while expanding the override cross-product.

**Probe/evidence.** Profile floor uses `(height, width, number of grid colors)` and passes in every band; independent probe sees 71/93/103 distinct profiles across 250 draws per band.

**Failure modes and limits.** Color 8 is reserved for the axis and 0 for background. The palette is semantically irrelevant; the generator intentionally does not teach a color remapping rule.

## D12 — Declare executable rivals and test complete lesson windows

**Decision.** Declare `above_only` and `grid_center` in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; bind witnesses to each; make `lesson_identifiable` reject a rival that fits every demo but changes the query.

**Original rationale.** Baseline comments named several informal rivals but provided no executable contract. The two selected rivals are the ones directly supported by canonical ambiguity and the observed baseline distribution.

**Alternatives rejected.** Rely only on witness frequency; enumerate generic transforms only; claim universal identifiability. Witness frequency did not catch the intermediate 10 ambiguous windows. Generic transforms miss task-specific shortcuts. Universal claims are not justified by a finite set.

**Probe/evidence.** G3; semantic gate; intermediate/final production censuses; reusable probe in `workspace/reference_probe.py`.

**Failure modes and limits.** Future plausible rivals must be added as executable functions and rerun against canonical pairs and all cyclic lesson starts. A rival equivalent to the authority on the entire documented domain should not be treated as a harmful ambiguity.

## D13 — Keep the Racket authority unchanged and pin it

**Decision.** Add `RULE_HASH = "586c575373f0"` and leave canonical data and the Racket program untouched.

**Original rationale.** Baseline omitted the pin. No reason was recorded.

**Alternatives rejected.** Edit the authority to match the one-way generator; rely on current catalog lookup without a pin. The former would corrupt a correct selected rule, while the latter permits unnoticed authority drift.

**Probe/evidence.** Lint, rule smoke, Racket lint, and authority sync all green; selected execution parity passes. Authority sync reports only an archival divergent raw-code copy, not divergence in the selected authority.

**Failure modes and limits.** The 12-character pin is a repository convention, not a collision-proof provenance record by itself; reports also retain full source/callable hashes.

## D14 — Add source-bound tests and an independent probe

**Decision.** Add selected-task tests covering canonical behavior, clipping, overrides, distributions, malformed inputs, mutation sensitivity, hash-seed determinism, real Racket parity, and all cyclic lesson starts. Add a standalone probe that reports distributions and optionally invokes the selected Racket authority.

**Original rationale.** No task-local tests or workspace probe existed.

**Alternatives rejected.** Depend only on the general battery; write a probe that silently falls back to Python if Racket is missing. The general battery does not auto-discover selected task tests, and silent fallback would turn a self-consistency check into a false parity claim.

**Probe/evidence.** 81/81 portable tests, fresh replay 81/81, and `checks/final/reference_probe-v2.json`.

**Failure modes and limits.** The independent Python geometry implementation can share a conceptual mistake with production code, which is why the optional Racket path fails closed and why canonical outputs are separately tested.
