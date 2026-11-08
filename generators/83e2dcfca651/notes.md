# Working notes: 83e2dcfca651

## Baseline and provenance

Selected baseline: version `2.0.1`, SHA-256 `bce9347c1357c5a84620eab258ba1f5bca1166f3ac80e8d3905ea6efacdbe1e8`. The retained associated-notes file was empty, so no prior return was used as task-specific evidence. The canonical authority already expressed the intended signed blue-to-red translation and was not changed.

The before battery was interrupted after four completed stages. It is not reported as a completed aggregate: self-check and rule smoke passed; lint failed because `RULE_HASH` was missing; defect lint failed because easy/medium/hard were byte-identical. Evidence is under `checks/before/`.

## Repair decisions

- Pinned canonical rule hash `94474e600431` and kept the Racket authority unchanged.
- Replaced the narrow fixed shape/vector tables and 300-attempt rejection loop with constructive placement over all fixed 4-connected polyominoes of size 3–6.
- Exposed five exact observable controls: `grid_h`, `grid_w`, `object_size`, `vector_dr`, and `vector_dc`; unknown, zero-vector, mistyped, and out-of-range controls fail loudly.
- Added real difficulty distributions while retaining exact canonical-size anchors in every band.
- Strengthened `self_check` to enforce palette, marker multiplicity, object size/connectivity, signed nonzero vector, in-bounds/disjoint translation, background target, and marker separation.
- Added a period-four quadrant schedule and `EXAMPLES_NEEDED = 4`. Any four consecutive demonstrations cover all signed quadrants; the declared `absolute_vector` rival fits all canonical examples but is refuted by generated negative-component witnesses.
- Added executable lesson, witness, rival, strict-profile, override-observer, and schedule hooks plus 45 portable tests and an independent Racket-backed geometry probe.

## Final evidence

Final generator SHA-256: `88689844b3f3b8902723cb7cb6f55168497f2b73db2f7991310bbb89ab15a44e`.

- Full after battery: 12/12 green, no advisory/failure/interruption (`checks/after/`).
- Portable selected-task stage: 45/45 passed (`checks/task-tests/`).
- Override matrix: 41,400/41,400 accepted draws across 460 cases, three bands, zero findings.
- Semantic smoke: 600/600 strict, 3/3 canonical accepted, 12/12 lessons identifiable, 0/60 ambiguous rotations.
- Production census: 300/300 lessons materialized; 1,500/1,500 rotations identifiable; 1,500 unique inputs; no materialization, hook, scoring, or ambiguity errors.
- Exposed solve: 4/4 visible examples on revision 1, earlier exposure `yes`, reference consultation `no`.

## Explicit limits

The semantic result is finite evidence against the named canonical-fitting rival, not a proof of unique human induction. The domain fixes colors to 1/2/3, one source object, one marker pair, and object sizes 3–6; it does not train multiple simultaneous vectors, multiple green components, target collisions, zero-axis vectors, or out-of-bounds clipping because those are outside this task grammar.
## Current reviewer considerations

Source SHA-256: `88689844b3f3b8902723cb7cb6f55168497f2b73db2f7991310bbb89ab15a44e`.

# Decisions for 83e2dcfca651

## D1 — Keep and pin the canonical authority

The Racket rule already implements the intended signed marker-vector translation and matches all canonical examples. I changed no canonical or base-solution bytes and pinned `RULE_HASH = "94474e600431"`. Replacing the rule would have expanded scope without evidence of an authority defect.

## D2 — Construct lawful scenes instead of retrying random scenes

The baseline selected from five shapes and ten vectors, then retried up to 300 times. The repair enumerates all fixed four-connected polyominoes of sizes 3–6, filters them for disjoint in-bounds translation, and then chooses a legal anchor and marker pair constructively. This makes failures explainable, removes stochastic exhaustion, and supports exact joint overrides. I rejected merely increasing the retry limit because it would preserve opaque incompatibilities.

## D3 — Expose only five exact, observable controls

The public axes are `grid_h`, `grid_w`, `object_size`, `vector_dr`, and `vector_dc`. Each can be reconstructed from the returned grid by `observe_overrides`; the 41,400-draw override matrix confirms all boundary and pairwise cases. Unknown, mistyped, out-of-range, and zero-vector values fail loudly. I did not expose shape identity or object coordinates because their finite naming contract would add maintenance cost without improving the core semantic test.

## D4 — Make difficulty real but keep one task grammar

Easy favors smaller grids, objects, and vector magnitudes; hard favors larger values; medium lies between. All bands retain the complete lawful support and exact overrides, and sample slots 0 and 1 anchor the two canonical dimension profiles. I rejected band-specific rules or palettes because difficulty should alter instance complexity, not the transformation being learned.

## D5 — Require four demonstrations and schedule all quadrants

All canonical examples use positive row and column displacement, so `abs(dr), abs(dc)` is a canonical-fitting shortcut. A deterministic period-four schedule emits down-right, down-left, up-right, and up-left vectors; `EXAMPLES_NEEDED = 4` means every consecutive lesson covers all quadrants. Random sign sampling was rejected because high marginal witness frequency does not guarantee every complete lesson contains a counterexample.

## D6 — Strengthen validation to the actual domain

`self_check` now enforces rectangular integer grids, palette `{0,1,2,3}`, exactly one marker of each type, one 3–6-cell four-connected green object, nonzero signed vector components, in-bounds and source-disjoint translation, background target, and marker separation. The weaker baseline check only counted marker colors and the presence of green, so malformed or semantically ambiguous grids could be admitted.

## D7 — Make semantic claims executable

The generator declares the canonical-fitting `absolute_vector` rival, a `signed_vector` witness, witness-to-rival mapping, canonical shortcut, lesson competitor, strict profile, and lesson hook. The portable helper independently computes geometry and calls public Racket authority. I did not claim universal identifiability: the evidence is explicitly finite and rival-bounded.

## D8 — Test behavior, not implementation details

The 45 tests cover canonical acceptance, Racket equivalence, exact joint overrides in every band, invalid controls, quadrant scheduling, difficulty separation, shape/vector diversity, purity, canonical rival fit, generated rival refutation, cyclic lesson starts, malformed grids, and semantic mutations. The tests load the generator by path and use `reviewer_support.find_root`, so the task-test stage can copy them into an isolated runtime.

## D9 — Preserve explicit domain limits

The generator intentionally excludes zero-axis vectors, clipping, source/target overlap, multiple green objects, multiple marker pairs, and colors outside 1/2/3. These are grammar boundaries rather than untested promises. Object sizes stop at six to keep ARC scenes legible while still providing broad fixed-polyomino morphology.
