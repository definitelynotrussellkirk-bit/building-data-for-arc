# Working notes: 2db2974cdb04

## Current rule and authority

The selected rule extracts holes, not filled objects: for each same-color nonzero 4-component, find global zero-regions whose every cell lies strictly inside that component's bounding box; paint those regions with the component color on an otherwise-zero output. Borders disappear. Canonical `RULE_HASH` is `c621ef85bf9e`; no Racket source changed in this review.

## Reversal from imported version 2.1.0

The imported summary said to fill frame interiors **and keep the borders**, and generated two hardcoded rectangles. Its rationale is unknown: this file contained no decisions and `evidence/associated_notes.jsonl` was empty. Canonical outputs contradicted that prose. Version 3.0.0 corrects the semantics and replaces the hardcoded layout/dead axes rather than changing the authority.

## Current input domain

- one or two distinct-colored closed objects on background 0;
- rectangular frames or exact rectangular frames with one straight two-cell outward stem;
- one enclosed global zero-region per object;
- disjoint object bboxes, while different-colored borders may be 4-adjacent;
- exact layouts 9×9, 9×11, 10×10, 10×12 and 12×14;
- exact observable controls: layout, object count, shape profile, edge/interior placement and touching/separated relation.

Generation enumerates finite feasible geometries and placements; it does not clip, retry to a cap, drop objects or silently swallow overrides. One object plus `contact_profile="touching"` is the only declared incompatible pair.

## Teaching contract

The three named rivals are `preserve_borders`, `bbox_interior`, and `largest_only`. `bbox_interior` fits every selected canonical pair, so stemmed cases supply generated counterexamples. The first stem witness was too broad: minimum-width stems sometimes produced the same answer as bbox filling. The intermediate semantic gate measured 51/60 successful rival checks and 1/48 ambiguous query rotations (`WORK/checks/after2/checks/2db2974cdb04_after_semantic_gate.log`). The final selector prefers actual bbox-counterexample geometry, and `stemmed_bbox_counterexample` fires only after an executable disagreement check.

The deterministic three-example cycle is: stemmed touching edge pair; rectangular separated interior pair; stemmed interior singleton. Every three consecutive examples cover all profiles. Focused tests hold out every position in four consecutive pairs. Final required-rotation semantic evidence is retained under `WORK/checks/after-final/`.

## Reproducers and probes

- `tests/test_generator.py`: independent oracle, canonical ownership, exact overrides, mutation rejection, distribution, rivals, all cyclic query positions and RNG-state checks.
- `workspace/hole_extraction_audit.py`: portable per-band/canonical JSON audit.
- `counterexamples/bbox-interior-shortcut/`: generated legal input, authoritative Racket output and disagreeing bbox-rival output.

## Known limits / open scope

The generator intentionally does not cover nested frames, open frames, arbitrary hollow polyominoes, more than two objects, or overlapping/interlocking bboxes. The declared rival set is finite and hypothesis-driven; passing it does not prove universal identifiability. Colors, sizes and positions vary to reduce fixed-role shortcuts, but no finite census excludes every undeclared model heuristic. Catalog approval and downstream model-learning impact remain outside this reviewer patch.
## Current reviewer considerations

Source SHA-256: `a966243cb3e7190492b43f480b8f3f2feea4f3a337b2debd4ab030311e04126b`.

# Decisions for `2db2974cdb04`

## D1 — Keep the selected Racket authority; correct the sampler and prose

**Prior choice.** Version 2.1.0 described the rule as filling each frame while preserving its border. Its original rationale is unknown: `notes.md` was empty and no associated note was retained. The selected canonical pairs instead remove every border and keep only enclosed holes on an otherwise zero grid.

**New choice.** Pin `RULE_HASH = c621ef85bf9e`, leave the Racket source unchanged, and make the Python sampler/documentation match the selected authority.

**Evidence.** The independent Python region oracle matches all five canonical pairs; authority sync and rule smoke are part of the final battery. The Racket source itself was not edited.

**Rejected alternative.** Changing the Racket rule to match the old prose would contradict every selected canonical output and was therefore not considered a lawful repair.

## D2 — Replace eight nominal controls with five exact, pixel-observable axes

The old axes included ignored controls, singleton domains, aliases and degenerate textures. The new exact axes are:

- `layout_profile`: 9×9, 9×11, 10×10, 10×12, or 12×14;
- `n_objects`: 1 or 2;
- `shape_profile`: rectangular or stemmed;
- `border_profile`: interior or edge-touching;
- `contact_profile`: separated or touching.

Every value is recovered by `observe_overrides`; unknown keys, wrong types and out-of-domain values fail loudly. The only declared incompatible joint setting is one object with `touching` contact.

**Why.** These controls correspond to visible task structure and cover the canonical variation: one/two objects, several exact sizes, edge contact, and different-colored touching frames. They also give future data assembly a falsifiable contract.

**Rejected alternative.** Keeping `palette_kind`, `texture`, `frame_size`, or `position_bias` as metadata-only knobs would preserve dead-axis leakage. Colors and detailed sizes still vary, but are stochastic layout details rather than falsely exact controls.

## D3 — Use closed frames plus a task-valid shortcut counterexample

Rectangular frames anchor the canonical manifold. A `stemmed` frame adds a straight two-cell outward stem while preserving exactly one enclosed hole. This expands the object bbox without necessarily enclosing the newly interior bbox cells, creating legal cases where “paint every zero inside the bbox” is wrong.

The first implementation overclaimed that every stem was a counterexample. Minimum cross-sections sometimes left no exterior-connected zero strictly inside the expanded bbox; the semantic gate measured only 51/60 successful rival disagreements and one ambiguous query rotation. The final selector prefers actual bbox-counterexample geometry whenever the requested joint axes permit it, and the witness predicate fires only after checking that the rival really differs.

**Rejected alternatives.** Arbitrary hollow polyominoes would broaden topology but make exact overrides, self-check recognition and small-grid feasibility much harder. Nested frames and open frames were removed because they are degenerate or ambiguous for this task rather than useful training branches.

## D4 — Construct scenes from a finite feasible geometry set

The generator enumerates lawful shapes and one/two-object arrangements, filters by requested contact and available canvas, then chooses deterministically with keyed RNG. Placement is selected from all positions satisfying edge/interior constraints. There are no capped rejection loops, clipping, dropped objects or fallback grids.

**Why.** The full advertised cross-product must either construct exactly or reject through a declared incompatibility. Finite enumeration is inexpensive at these grid sizes and makes boundary combinations auditable.

**Limitation.** Generated objects have disjoint bounding boxes. Canonical touching is represented, but interlocking or nested bboxes are intentionally outside the generator domain.

## D5 — Make `self_check` a structural recognizer, not a replay check

The validator now checks rectangular integer ARC grids; one or two distinct-colored same-color 4-components; rectangular or exact two-cell-stemmed frames; disjoint bboxes; and exactly one global zero-region wholly strict-inside each object bbox. It accepts all canonical inputs, including the single object, area-two hole, edge-touching objects and different-colored touching objects.

**Mutation coverage.** Focused tests reject malformed grids, solids and opened frames; the official self-check gate exercises canonical acceptance and mutation sensitivity.

**Known boundary.** `strict_canonical_like` intentionally means strict task-validity, not literal replay of canonical rectangles. The generated stem branch is broader than the five public examples but obeys the selected Racket semantics.

## D6 — Declare executable rivals and precise witnesses

Declared competitors are:

1. `preserve_borders` — fills holes but retains input borders;
2. `bbox_interior` — paints every input-zero cell strict-inside each object bbox;
3. `largest_only` — extracts only the largest object's hole.

Witnesses respectively prove border removal, a verified stemmed bbox counterexample, and multiple objects. `bbox_interior` is also a `CANONICAL_SHORTCUT` because it matches every selected canonical pair; generated counterexamples are therefore required.

**Scope.** This is finite, hypothesis-driven evidence. It does not prove uniqueness against every possible solver. Undeclared color-rank, position, count and memorization shortcuts are reduced by randomized colors, positions, sizes and exact layouts but are not exhaustively enumerated.

## D7 — Use a three-profile cyclic curriculum and test all held-out positions

The deterministic profiles are:

1. stemmed, touching pair at an edge;
2. separated rectangular pair in the interior;
3. separated stemmed singleton in the interior.

Every three consecutive samples contain all profiles. Three demonstrations are required, and focused tests hold out every one of four consecutive pairs as the query. The final semantic stage is run with query rotations required, not merely diagnostic.

**Why.** One profile defeats all three named rivals, while the others prevent the lesson from collapsing to “always multiple,” “always touching,” or “always stemmed.” A cyclic schedule gives a cheap exhaustive start-offset argument in addition to sampled lesson checks.

**Limitation.** The exported assembler must preserve three demonstrations. Fewer demonstrations are rejected by `lesson_identifiable`.

## D8 — Anchor scale in every difficulty band without making bands identical

Easy draws use the four canonical dimensions; medium adds 12×14; hard weights larger profiles and larger geometry. All bands retain exact canonical dimension/palette support. Difficulty changes the actual distribution rather than only a label.

**Rejected alternative.** A dedicated canonical-only band would leave hard or medium with zero exact support and permit scale to become a spurious task identifier.

## D9 — Retain independent tests and a reusable audit tool

`tests/test_generator.py` contains an independent region oracle, canonical acceptance, exact override, invalid-input, diversity, curriculum-rotation, rival and RNG-state regressions. `workspace/hole_extraction_audit.py` independently replays canonical pairs and samples every band, reporting axes, exact-profile hits, uniqueness and declared-rival disagreement as JSON.

The audit tool is diagnostic: the selected Racket program remains the label authority, and the final official battery/task-test/lesson-census artifacts are the acceptance evidence.
