# Working notes: 59a9a5c505fb

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2ae25bb282a604f1d8266bed437a8b553f45d8b563b3aef73e5759fc4b21f274`.

# Decisions for 59a9a5c505fb

## D1 — Preserve the bbox-count rule

**Choice.** Keep the selected canonical Racket behavior unchanged: find every nonzero 4-connected component, take its bounding box, and output at each cell the number of boxes containing that coordinate.

**Original rationale.** Rule smoke and canonical examples already showed correct behavior. The defect was distributional: the v2.1.0 sampler produced only complete nested rectangle frames, not a wrong oracle.

**Alternatives considered.** Rewriting the Racket rule, adding special cases for sparse objects, or narrowing the documented rule to rectangle frames.

**Probe.** Independent Python-oracle and real-Racket parity tests over every canonical pair and generated profile; final task tests 46/46.

**Failure modes / limitation.** Racket parity validates sampled inputs and canonical pairs, not every lawful grid. The general rule still assumes the selected authority’s 4-connected object convention.

## D2 — Replace eight misleading controls with one exact semantic axis

**Choice.** Expose only `scene_profile`, with exactly four observable values. Reject unknown keys and invalid values explicitly.

**Original rationale.** The old controls mixed geometry, palette aliases, band-constrained sizes, and degenerate textures. The before override gate produced 14,817 findings; many advertised values could not be honored in all bands, several controls were dead or correlated, and unknown keys were silently accepted.

**Alternatives considered.** Preserve all old names and add incompatibility declarations; add separate size, object-count, morphology, orientation, and palette controls; keep legacy degenerate textures.

**Why rejected.** Retaining the old surface would make the contract larger than the behavior and invite new hidden interactions. Exposing internal randomness such as orientation would add override obligations without improving lesson semantics. Degenerate examples are useful as diagnostics but not required production controls.

**Probe.** The final override report checks all advertised exact values across bands and seeds; 450/450 accepted cases produced no mismatch, provenance, self-check, or unknown-key finding.

**Failure modes / limitation.** Size and orientation remain internal keyed draws and cannot be requested directly. This is deliberate; consumers needing those controls would require a later contract extension with tests.

## D3 — Use a four-profile deterministic cycle

**Choice.** Schedule `nested_frames`, `nested_sparse`, `crossing_sparse`, `crossing_mixed` by `sample_index mod 4`.

**Original rationale.** A small deterministic period makes lesson-level teaching guarantees testable. With three demonstrations and one query, every hold-one-out rotation keeps at least one crossing profile and at least two non-frame profiles.

**Alternatives considered.** Independent random profile sampling; a two-profile frame/sparse alternation; a three-profile schedule; a longer stochastic curriculum.

**Why rejected.** Independent sampling can create all-frame lessons. A two-profile or three-profile cycle does not simultaneously guarantee canonical support, sparse morphology, and non-nested boxes under every query rotation. A longer schedule adds state without improving the minimum guarantee.

**Probe.** Exhaustive local tests cover every cyclic start and every query position in all three bands. The semantic gate checked 48 rotations; the large census checked 1,200 rotations with zero declared-rival ambiguity.

**Failure modes / limitation.** The downstream assembler must preserve consecutive sample indices for the schedule guarantee. The source-bound census exercised the production sampler and all hold-one-out positions, but did not enumerate arbitrary nonconsecutive batch assembly.

## D4 — Retain exact canonical size/palette profiles

**Choice.** Draw only from the five observed canonical `(height, width, number-of-colors)` profiles, with band-specific subsets.

**Original rationale.** The repair should broaden semantics rather than drift to unobserved scales. Exact canonical support also makes profile-floor evidence straightforward.

**Alternatives considered.** Broad rectangular ranges, arbitrary object counts from 2–5, or fixed 11×11 grids.

**Why rejected.** Broad ranges create unanchored extrapolation and a larger override surface. More objects change output-value support beyond the canonical maximum. One fixed size would reduce diversity and fail to represent all canonical profiles.

**Probe.** Profile floor: 20/20 exact hits in each band, 60/60 overall; 0/5 canonical inputs rejected. Semantic gate strict canonical-like rate 145/600 = 24.17%, above the declared 20% floor.

**Failure modes / limitation.** There is no evidence here for larger grids or more than three objects. Those should be a separately reviewed expansion.

## D5 — Choose sparse L-shapes and crossing boxes as counterexamples

**Choice.** Use connected top-left and bottom-right L-shapes for sparse objects; use two incomparable overlapping bounding boxes for crossing profiles; include one mixed frame/sparse case.

**Original rationale.** An L-shape leaves most of its bbox interior blank while remaining a simple connected object. Crossing boxes directly refute the assumption that all boxes form a strict nesting chain. Mixed morphology prevents a learner from using a global “scene type” switch.

**Alternatives considered.** Random walks, disconnected corner markers, arbitrary polyominoes, filled rectangles, or only sparse nested shapes.

**Why rejected.** Random walks complicate self-checking and reproducibility. Disconnected markers alter object parsing. Filled rectangles do not distinguish bbox filling from visible cells. Nested sparse shapes alone leave the nesting-only shortcut alive.

**Probe.** Frame-only witness 455/600; crossing witness 295/600; bbox-interior witness 600/600. Each claimed witness disagreed with its rival in all 60 sampled rival checks.

**Failure modes / limitation.** A finite template bank can still be recognized as a template family. Dihedral transforms, placements, colors, sizes, and object count provide variation, but this does not equal unrestricted connected-shape diversity.

## D6 — Make the validator semantic rather than cosmetic

**Choice.** `self_check` verifies rectangular ARC grids, exactly one connected component per nonzero color, two or three objects, common bbox intersection, and profile-specific diagnostic properties when metadata is available.

**Original rationale.** The old validator mainly protected the nested-frame construction; it did not define the general bbox-count domain strongly enough for audit counterexamples and teaching witnesses.

**Alternatives considered.** Validate only syntax; infer no profile; require every object to be a frame.

**Why rejected.** Syntax-only checks permit mislabeled or unteachable inputs. Frame requirements would reproduce the original defect. Profile-aware diagnostics make generated claims falsifiable without narrowing the general oracle.

**Probe.** Tests deliberately submit disconnected same-color objects, nonoverlapping boxes, ragged rows, invalid colors, and empty inputs. The 600-draw semantic census had zero crashes and all generated inputs passed.

**Failure modes / limitation.** `self_check` is not a formal proof that every input has a unique intended human interpretation; it establishes the declared generator domain and witness conditions.

## D7 — Declare the canonical-fitting rivals explicitly

**Choice.** Retain `frame_fill_only` and `nested_chain_only` as canonical shortcuts, and add `visible_cells_only` as a lesson competitor.

**Original rationale.** Both first rivals fit all five canonical pairs. The third is a common local-cell shortcut and is cheaply refuted by every generated profile.

**Alternatives considered.** Rely only on generic transforms; enumerate a much larger speculative rule library; declare no rivals and use witness frequency alone.

**Why rejected.** Generic geometric transforms do not target the observed ambiguity. A huge speculative library would be expensive and noisy. Witness frequency without executable rival predictions does not establish lesson discrimination.

**Probe.** Tests first verify that each claimed canonical shortcut really fits every usable canonical pair, then verify every production lesson and rotation refutes the declared competitors.

**Failure modes / limitation.** Undeclared rivals can remain. This is why `QUESTION_ANSWER.md` recommends an independent automatic rival-mining gate.

## D8 — Synchronize active authority text without changing semantics

**Choice.** Remove one explanatory comment from selected base `target_code` so it exactly equals the existing `raw_code` and canonical program.

**Original rationale.** The before authority-sync and defect-lint stages flagged two active exact-text groups, although execution parity passed and comment-stripped text was identical.

**Alternatives considered.** Add the comment to canonical and raw sources; waive the divergence; modify the executable rule.

**Why rejected.** Canonical editing was unnecessary. A waiver would leave a blocking gate and duplicate authority. Copying the already-selected canonical/raw text is the smallest nonsemantic correction.

**Probe.** Final defect lint, authority sync, and rule smoke all pass. Canonical `RULE_HASH` remains `058f695b6f59`.

**Failure modes / limitation.** This changes a selected base artifact’s exact SHA, so the return correctly includes it as a Racket component even though behavior is unchanged.

## D9 — Use test-first implementation and preserve the failure

**Choice.** Write the task-local suite before replacing production behavior, run it on untouched source, then implement to green.

**Original rationale.** The key defect is easy to “fix” cosmetically while preserving shortcut ambiguity. A RED run demonstrates that the tests distinguish old and new behavior.

**Alternatives considered.** Add tests after implementation or rely only on the general battery.

**Why rejected.** Tests-after would not prove that the assertions detect the original defect. The general battery samples only a small number of lessons and does not automatically discover selected-task tests.

**Probe.** RED: 38 failed, 8 passed. Final selected-task stage: 46 passed, 0 failed/errors/skips.

**Failure modes / limitation.** The test suite is focused on this generator and its declared competitors; it is not a repository-wide regression run.

## D10 — Stop after finite, source-bound evidence rather than claim proof

**Choice.** Stop after the full battery, 46 focused tests, 600-draw semantic census, 300-lesson/1,200-rotation census, and post-repair solve all passed.

**Original rationale.** These checks directly cover the identified failure modes and required duties. Further brute-force sampling would add confidence but not change the core limitation that the rival family is finite.

**Alternatives considered.** Enumerate every seed, every connected shape, or attempt a universal identifiability proof.

**Why rejected.** The input space is too large, and universal induction is not established by finite enumeration. The honest remaining limitation is documented instead.

**Stopping condition.** No blocking final check failed; no generator edit occurred after the frozen post-repair solve.
