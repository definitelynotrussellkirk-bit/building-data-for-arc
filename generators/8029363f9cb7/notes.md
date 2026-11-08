# Working notes: 8029363f9cb7

## Current intended rule

A single red (`2`) source launches a beam **to the right**, independent of its position. Empty cells traversed by the beam become cyan (`8`). Slash mirrors (`3`) and backslash mirrors (`4`) reflect the beam, and the first gray (`5`) wall—including the outer frame—stops it. Off-path mirrors and interior walls are distractors and remain unchanged.

The selected Racket authority did not change in review `review-1d82b895d1d33919`; `RULE_HASH` remains `a08bfbc3cb49`.

## Reversed baseline decision: fixed left-edge source

The 4.0.0 baseline placed every generated source at interior column 1, matching all five canonical inputs. This left a strong canonical-fitting shortcut unchallenged: launch horizontally away from the nearest vertical frame. It matched 5/5 canonical pairs and all 1,200 measured baseline draws. The earlier audit in `evidence/review_index.json` also showed that the old `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)` declaration was false because none of those declared rivals fit every canonical pair.

Version 5.0.0 replaces that decision with a balanced source-side schedule. Every four-example curriculum window contains sources near both vertical frames, while all sources still launch right. The only declared canonical shortcut is now the actual nearest-frame rival. A minimal generated refutation is retained at `counterexamples/review-1d82b895d1d33919/source_launch_shortcut.json`.

## Curriculum and validation decisions

- Twelve fixed semantic profiles remain, four per difficulty band.
- Each four-slot band now contains two left-side and two right-side sources.
- Every four consecutive demonstrations expose both mirror laws, both wall-stop classes, an off-path mirror, a multi-reflection route, at least two shapes, and both source sides.
- The medium second profile gained an off-path mirror so every allowed query rotation retains a distractor witness.
- `scene_profile` remains the only public exact axis; it is observable from the returned grid.
- Right-side sources use column `width - 5`, leaving a launch cell, a first mirror, and post-reflection room while making the right frame strictly nearer.

## Evidence and current limits

The source-bound shortcut probe reports 600 nearest-frame disagreements in 1,200 final draws, balanced 600 left / 600 right, and 0/1,200 surviving four-demo windows. The larger census reports 0/300 production ambiguities and 0/1,500 query-rotation ambiguities against the declared competitors. Focused task tests pass 13/13 and the complete battery passes 12/12 at generator SHA-256 `6a09172dbea66502b5f29d9e2311a0a702d586f8b06f0a4382e7beefa50928af`.

The grammar is intentionally narrower than the full oracle-valid space: source columns use two anchors, and route geometry comes from twelve canonical-linked profiles. Finite checks against declared rivals do not prove universal induction; future profile edits should rerun the source-bound probe and required query-rotation census.
## Current reviewer considerations

Source SHA-256: `6a09172dbea66502b5f29d9e2311a0a702d586f8b06f0a4382e7beefa50928af`.

# Decisions for `8029363f9cb7`

## D1. Treat the nearest-frame launch rule as the primary defect

**Baseline choice.** Version 4.0.0 copied the canonical placement pattern and put
the red source at interior column 1 in every generated scene.

**Why reversed.** The executable rival “launch horizontally away from the
nearest vertical frame” matches all 5 canonical demonstrations, all 1,200
measured baseline draws, and all 1,200 tested four-demo windows. This is stronger
than the already-known metadata defect in the old `CANONICAL_SHORTCUTS` mapping:
it is a plausible semantic rule that a learner could actually use successfully.

**Alternative rejected.** Merely removing the false shortcut declarations or
adding the nearest-frame function to `CANONICAL_SHORTCUTS` would make metadata
more truthful but would not teach the intended fixed-rightward launch rule.

**Evidence.** `checks/probes/source-launch-baseline.json` and the prior lead in
`repo/generators/8029363f9cb7/evidence/review_index.json`.

## D2. Change source placement, not the Racket authority

**Choice.** Preserve the selected canonical Racket rule and `RULE_HASH =
"a08bfbc3cb49"`; change only the generator’s lawful input distribution and
semantic declarations.

**Rationale.** The intended rule is already coherent and the selected authority
passes canonical parity. The defect is absence of a counterfactual source
position. A right-side source whose beam still launches right cleanly separates
the intended rule from the rival without redefining mirror behavior or labels.

**Alternative rejected.** Altering the rule to launch away from the nearest
frame would validate the shortcut by changing the task, conflict with the
canonical rightward semantics, and unnecessarily modify reference authority.

## D3. Use fixed source-side profiles rather than a new free axis

**Choice.** Add `source_side` to the twelve internal semantic profiles and keep
`scene_profile` as the sole public exact axis.

**Rationale.** Source side is part of the curriculum witness structure, not an
independent nuisance variable. Encoding it in profiles lets every four-slot band
make explicit guarantees about source sides, mirror types, wall stops,
reflections, shapes, and distractors. `observe_overrides` remains exact and
truthful.

**Alternative rejected.** A public `source_side` axis would enlarge the joint
override contract and permit callers to request all-left lessons, recreating the
shortcut unless lesson assembly imposed another layer of restrictions.

## D4. Balance each four-slot band two-left/two-right

**Choice.** Every difficulty band contains two left-side and two right-side
profiles; all sources still launch right.

**Rationale.** One right-side witness per four examples refutes the nearest-frame
rival for the ordered production query, but it is not robust when any member of a
five-pair bundle may become the query. Two decisive source positions keep a
right-side witness among four demonstrations after any single holdout.

**Failed alternative retained.** The first implementation added only one
right-side profile per band. The new rotation regression failed 1/13 tests
because some query positions removed the sole witness. Evidence:
`checks/tdd-rotation-red/`.

## D5. Put right-side sources at `width - 5`

**Choice.** Use interior column `width - 5` for right-side profiles.

**Rationale.** It makes the right frame strictly nearer while preserving one
launch cell, the first mirror location, and enough post-reflection room for the
existing constructive route templates.

**Failed alternative retained.** `width - 4` caused geometry failures in the
first implementation because the template lacked the required horizontal room.
Evidence: `checks/tdd-green-1/` followed by the passing
`checks/tdd-green-2/`.

## D6. Add an off-path distractor to the medium right-side profile

**Choice.** The medium `outer_three_turn` right-side profile now includes an
off-path slash mirror.

**Rationale.** The four-demo production window already carried a distractor, but
one held-out query rotation could remove the only distractor witness. Adding a
second one preserves the declared lesson contract at every query position while
remaining rule-lawful.

**Alternative rejected.** Weakening `lesson_identifiable` or omitting the
rotation test would hide a real curriculum dependency rather than repairing it.

## D7. Declare only the rival that actually fits the canonical examples

**Choice.** `CANONICAL_SHORTCUTS` contains
`launch_away_from_nearest_vertical_frame`; the other executable competitors stay
in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.

**Rationale.** A canonical shortcut declaration should mean the function matches
all labeled canonical pairs. The old blanket copy of semantic rivals violated
that meaning and could inflate semantic evidence.

**Alternative rejected.** Keeping the old names for backward compatibility
would preserve a false contract. The functions remain available as semantic
competitors, so no useful lesson check was lost.

## D8. Require arbitrary query-position robustness

**Choice.** Run the semantic gate with
`--require-rotations-identifiable` and the 300-lesson census with
`--rotate-query --rotation-policy require`.

**Rationale.** The repaired four-slot schedule is intended to support each
member of the materialized five-pair bundle as query. Therefore rotations are a
required contract, not a diagnostic observation.

**Measured result.** 0/300 production ambiguities and 0/1,500 rotated-query
ambiguities against declared rivals, with 1,230 unique exact inputs. Evidence:
`checks/lesson-census-final.json`.

## D9. Retain a direct Racket-checked witness

**Choice.** Store the generated seed-0/sample-1 right-side case and execute the
selected canonical Racket authority on it.

**Rationale.** The reusable Python probe is useful for large finite sampling,
but the question asks how the exact output was checked. The Racket receipt binds
the witness to rule hash `a08bfbc3cb49` and final generator hash `6a09172d…`.

**Evidence.**
`repo/generators/8029363f9cb7/counterexamples/review-1d82b895d1d33919/source_launch_shortcut.json`
and `checks/probes/source-launch-counterexample-racket.json`.

## D10. Keep the grammar bounded and document the residual restriction

**Choice.** Retain twelve canonical-linked profiles and two source-column
anchors rather than generalizing to arbitrary valid beam mazes.

**Rationale.** The assignment calls for a generator repair, not a new exhaustive
maze constructor. The bounded grammar keeps labels, route termination, exact
profile observation, and lesson composition auditable.

**Limitation.** A learner may still exploit an undeclared profile-specific
regularity. The final probe, required semantic gate, and 1,500 query rotations
cover the declared rivals only; they do not prove universal induction. Future
changes should preserve the exact witness and rerun these source-bound checks.

## D11. Audit targets remain unchanged

The audit findings for `6e9bc73dbb78` and `446c18f3b7f4` are evidence only.
No audited generator source was edited, and neither audit is an approval or a
claim that all other behavior was examined.

## D12. Use the supported staged task-test command for fresh replay

**Choice.** Treat `python3 review.py run ... check 8029363f9cb7 --stage
task_tests` as the authoritative fresh regression invocation.

**Rationale.** A direct repository `pytest` attempt was retained and exited 2
during collection because the frozen fixture needs the legacy staged `scripts`
namespace and the new test imports the staged per-puzzle package. The official
checker creates both namespaces, binds their hashes in `RUNTIME_MANIFEST.json`,
and passed all 13 tests on the exact replayed generator bytes.

**Additional replay check.** The exact packaged probe was also run from the fresh
source and reproduced 600/1,200 rival disagreements and 0/1,200 surviving
windows. Evidence: `checks/fresh-replay/replay.json`.
