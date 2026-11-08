# Working notes: 5cf662353a2a

## Intended rule

Treat every nonzero, non-1 4-connected same-color component as an object. Sort objects by increasing cell count, normalize each bounding box, and bottom-align them over the bottom-row color-1 markers from left to right. The selected Racket authority is unchanged and pinned by `RULE_HASH = "da86a7976cec"`.

## Review finding and reversal

Version 2.2.0 advertised nine axes, but several were ignored, clamped by difficulty, or represented invalid degenerate grids. It silently accepted unknown override keys, had no exact observer, generated zero canonical profiles in the pinned 60-draw floor, and declared no semantic rival or lesson contract. Canonical examples also admitted the plausible shortcut “sort by bounding-box area” because their cell-count and box-area orders coincide.

The prior choice of broad free-form dimensions, random-walk motifs, retry placement, and texture aliases was replaced by six named constructive layout profiles plus `palette_start`. Every axis is exact and observable from returned pixels. Finite exhaustive placement replaces capped retries, and the marker geometry is checked so both the intended placement and the declared rival remain in bounds.

## Curriculum decision

Every generated instance contains a size-4 T tetromino (box area 6) and a size-5 line (box area 5). Thus cell-count order and bounding-box-area order disagree on every draw. `bbox_area_sort` is declared in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, bound to the `cell_count_vs_bbox_area` witness, and checked by `lesson_identifiable` under query rotation.

The six-position default schedule includes both canonical profiles `(10,12,5)` and `(11,13,5)` in every band. Broader 3- and 4-object profiles retain dimension, placement, orientation, color assignment, and palette variation without weakening the teaching witness.

## Evidence and reproducibility

- Focused tests: `tests/test_generator.py` (80 cases).
- Reproducer/tool: `workspace/probe_size_order.py`.
- Minimal counterexample: `counterexamples/cell-count-vs-bbox/`; the public Racket apply output matches the independent cell-count oracle and differs from the rival in 12 cells.
- Aggregate after battery: 12/12 green at generator SHA-256 `c262f073c82d7099ebb17e4bd18eb5e55277ac1c2c371f19e6ad738017d3ccc4`.
- Lesson census: 300/300 lessons materialized, 1,200 unique inputs, zero production or query-rotation ambiguities against the declared rival.

## Assumptions and limits

The checker intentionally owns the observed task grammar used by canonical and generated inputs: one uniquely colored connected object per marker, distinct cell counts, and a non-clipping sorted drop. It does not claim to characterize every input on which the Racket program returns some grid. Rival evidence is finite and task-linked; it establishes the declared bounding-box shortcut is taught against, not universal identifiability against every imaginable hypothesis.

No shared source or Racket authority was edited. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c262f073c82d7099ebb17e4bd18eb5e55277ac1c2c371f19e6ad738017d3ccc4`.

# Decisions for `5cf662353a2a`

Final generator version: `3.0.0`
Final generator SHA-256: `c262f073c82d7099ebb17e4bd18eb5e55277ac1c2c371f19e6ad738017d3ccc4`
Selected rule hash: `da86a7976cec` (unchanged)

## D1 — Keep the selected Racket authority unchanged

**Prior choice and rationale.** The assigned package already contained a selected rule that sorts non-marker objects by cell count, normalizes them, and drops them over markers. The original rationale beyond the canonical task is unknown.

**Decision.** Treat that rule and its canonical outputs as the authority; repair only the generator, tests, notes, and task-local evidence.

**Alternatives considered.** Editing the Racket program to match easier generated geometry, or changing the canonical row, would have hidden a data-generation defect behind a rule change. Neither was justified by a rule-smoke failure.

**Probe/evidence.** The public rule-smoke and authority-sync stages are green in the final battery. The deterministic counterexample's Racket output equals an independently implemented cell-count oracle.

**Failure modes and limits.** Passing canonical and generated examples does not prove the rule is correct for arbitrary malformed grids. The task-owned validator deliberately defines the supported training grammar more narrowly.

## D2 — Replace nine broad controls with two exact observable controls

**Prior choice and rationale.** Version `2.2.0` advertised dimensions, palette, texture, object count, position, and other generic axes. Several were ignored, clamped by difficulty, singleton domains, or aliases for invalid degenerates; the historical design intent is otherwise unknown.

**Decision.** Expose only `layout_profile` and `palette_start`. A profile name fixes height, width, marker columns, and marker count; `palette_start` fixes the consecutive object-color range. Both can be recovered from returned pixels. Reject every unknown override and every invalid type/value.

**Alternatives considered.** Keeping free-form `grid_h`, `grid_w`, and object-count axes would require a much larger compatibility matrix and marker-placement solver. Retaining generic palette/texture labels would add names that did not change the actual task semantics. I preferred a smaller truthful contract over nominal combinatorial breadth.

**Probe/evidence.** The strict override matrix is green for all profiles, palette starts, difficulty bands, joint combinations, invalid values, and the unknown-key probe. Focused tests independently observe each requested control from pixels.

**Failure modes and limits.** Named profiles reduce geometric support to six layouts. This is a conscious restriction, documented in the generator and notes, rather than an accidental hidden clamp.

## D3 — Schedule canonical profiles in every difficulty band

**Prior choice and rationale.** The assigned source sampled broad dimensions but hit zero canonical profiles in the pinned profile-floor check. No deliberate canonical schedule was documented.

**Decision.** Use a six-position deterministic profile schedule. Every band contains both canonical profiles `(10,12,3 markers)` and `(11,13,3 markers)`; harder bands include more large/four-object profiles. Seed is nuisance-only for profile selection, while sample index controls the schedule position.

**Alternatives considered.** Weighted random selection could satisfy the floor statistically but would leave avoidable flaky coverage. A single canonical-only layout would pass the floor but reduce useful diversity.

**Probe/evidence.** Focused tests inspect every 20-draw band. The shared profile-floor stage is green, and the 300-lesson census records all six schedule residues.

**Failure modes and limits.** The schedule has period six. The census covers consecutive starts and all observed residues but does not enumerate every seed-dependent hypothesis because profile selection intentionally ignores seed.

## D4 — Make the semantic distinction present in every ordinary draw

**Prior choice and rationale.** The three canonical pairs order objects the same way by cell count and by bounding-box area. The old generator did not declare or force a separating example.

**Decision.** Include a four-cell T tetromino (box area 6) and a five-cell line (box area 5) in every generated input. The intended size order puts 4 before 5; the plausible box-area shortcut reverses them. Three-object profiles use sizes 3,4,5; four-object profiles use 2,3,4,5.

**Alternatives considered.** Injecting a witness only once per lesson would preserve more shape freedom but make lesson assembly and rotations fragile. Randomly hoping for an order conflict would not support an exact teaching guarantee. Adding many rivals at once would overstate what was actually validated.

**Probe/evidence.** `workspace/probe_size_order.py` first verifies that every declared rival fits all canonical labels, then writes a source-hashed witness. The Racket-labelled minimal counterexample differs from the rival in 12 cells. Every one of 600 strict semantic draws fired the witness in the battery, and all 300 census lessons refuted the rival.

**Failure modes and limits.** This design specifically defeats `bbox_area_sort`. Fixed size/shape families may still permit an undeclared extent or shape-identity heuristic. The reports state that finite limitation rather than claiming universal identifiability.

## D5 — Randomize shape orientation, placement, and color assignment without weakening the witness

**Prior choice and rationale.** Version `2.2.0` used random-walk motifs and retry placement to obtain broad appearance variation. That approach made guarantees hard to state and occasionally made rival placements clip.

**Decision.** Draw from finite dihedral variants for dominoes, triominoes, and T tetrominoes; keep the five-cell line vertical so it fits every rightmost canonical marker. Shuffle colors across sizes and independently shuffle candidate placements. Reserve a one-cell moat between input objects and above markers.

**Alternatives considered.** Allowing every pentomino would improve visual diversity but several variants do not fit all declared marker columns after normalization. Widening every profile solely to accommodate them would move farther from canonical geometry. A horizontal five-line was tested indirectly and rejected because it clips on the rightmost canonical marker under the rival ordering.

**Probe/evidence.** The second TDD green attempt retained 20 failures that localized rival-side clipping. Marker columns and the vertical line choice were adjusted once, after which all 80 focused tests and all shared stages passed.

**Failure modes and limits.** The vertical five-line is visually distinctive and may itself become a shortcut. Color shuffling prevents a pure color-rank shortcut, but shape-family expansion remains a future improvement.

## D6 — Use finite exhaustive placement instead of capped random retries

**Prior choice and rationale.** The old source retried random placements and could silently return a reduced or poorly characterized instance. Its exact fallback semantics were not a useful training contract.

**Decision.** Enumerate legal origins, randomize their order, and backtrack until all objects are placed. Raise if a declared profile is unsatisfiable; never silently drop an object or shrink the requested configuration.

**Alternatives considered.** Increasing retry counts would reduce but not remove failure probability. Deterministic fixed positions would simplify construction but sacrifice nuisance variation.

**Probe/evidence.** Final strict/self-check, distribution, diversity, and 1,200-pair census runs have zero materialization errors. Focused tests check deterministic replay, fresh copies, separation, counts, and output fit.

**Failure modes and limits.** Backtracking cost grows combinatorially if profiles or object families expand substantially. For the current small grammar it is bounded and fast.

## D7 — Own a strict task grammar in `self_check`

**Prior choice and rationale.** The baseline checker did not fully encode one object per marker, unique sizes, marker placement, non-clipping authoritative output, or the semantic witness.

**Decision.** Validate rectangular ARC grids, bottom-row separated markers, one uniquely colored 4-connected object per marker, distinct sizes, no marker/object contamination, non-clipping cell-count output, and the box-area ordering conflict.

**Alternatives considered.** Accepting every grid on which the Racket program happens to return something would make generation guarantees impossible to state. Conversely, attempting to formalize all conceivable task-valid ARC grids would be unnecessary for this generator review.

**Probe/evidence.** Focused malformed/degenerate cases and shared self-check/strict-profile stages pass. `MIN_STRICT_FRAC=1.0` is met.

**Failure modes and limits.** The checker is a generation-domain contract, not a theorem characterizing the entire Racket function domain. That distinction is explicit in `notes.md`.

## D8 — Declare rivals and require three-demo lesson identifiability under rotation

**Prior choice and rationale.** The assigned source had no `strict_canonical_like`, semantic witnesses, rivals, canonical shortcuts, lesson competitors, or `lesson_identifiable` hook.

**Decision.** Declare the same pure deterministic `bbox_area_sort` function in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; bind it to `cell_count_vs_bbox_area`; require three demonstrations; and check all possible held-out query positions for every four-pair bundle.

**Alternatives considered.** A single-grid witness frequency is insufficient because lesson windows can omit the witness. Ordered-only checking would leave query-position sensitivity unmeasured. More demonstrations were unnecessary because every generated pair already distinguishes the declared rival.

**Probe/evidence.** The shared semantic smoke test checked 12 lessons and 48 rotations. The larger required-rotation census checked 300 production lessons and 1,200 rotations with zero ambiguity or scoring/materialization errors.

**Failure modes and limits.** The downstream curriculum is certified only against declared rivals. Query rotation reuses each materialized bundle and does not enumerate every possible cyclic window or unknown hypothesis.

## D9 — Preserve a reusable authoring probe and minimal counterexample

**Prior choice and rationale.** There was no source-bound tool for future reviewers to verify canonical rival fit or regenerate the witness.

**Decision.** Add `workspace/probe_size_order.py` and the four-file counterexample directory. The probe discovers rivals from current declarations rather than hard-coding only a report-time name.

**Alternatives considered.** Keeping the logic only in tests would make manual authoring and audit reuse harder. Copying full review logs into task notes would create noisy, stale documentation.

**Probe/evidence.** `checks/probe-size-order.txt` records canonical fit, source hash, and the 12-cell divergence. The focused tests cover the same behavior independently.

**Failure modes and limits.** The probe reads canonical answers, so its README explicitly forbids use during visible-only solve episodes.

## D10 — Preserve failures and distinguish process interruption from test failure

**Prior choice and rationale.** The packet requires retained failed evidence. The exact aggregate battery's first process was terminated by the caller's command-output cap after checkpointing three green stages.

**Decision.** Retain all TDD failures and the interrupted aggregate attempt, then resume only after the runner verified unchanged source, runtime, and policy hashes. Present only the completed resumed aggregate as final evidence.

**Alternatives considered.** Deleting failed attempts would make the red/green and debugging trail unverifiable. Calling the interrupted result a pass would be inaccurate.

**Probe/evidence.** `checks/after/attempts/0001/` contains the interruption; `checks/after-resume-console.log` and `checks/after/result.json` show the hash-checked completion.

**Failure modes and limits.** The retained logs are process evidence, not additional semantic coverage.
