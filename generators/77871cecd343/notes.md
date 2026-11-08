# Working notes: 77871cecd343

## Final repair: version 2.1.0

Baseline SHA-256 `75cde447e24b9fbeeb6ad039887fdadcbe9a58db933c5fc6e27b7c9a32214bbb` sampled only 1–3 isolated color-1 cells in the upper-left quadrant, rejected 3/5 canonical inputs, omitted the rule pin, silently ignored/accepted controls, and declared no semantic contract. The final generator SHA-256 is `5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca`.

The repaired sampler constructs the actual task grammar: exactly one full color-9 row and column, a 3–8-cell 4-connected color-1 shape in any one quadrant, and enough room for all three reflections. `self_check` validates the whole advertised domain and accepts all five canonical inputs. `observe_overrides` recovers all six exact controls from pixels.

## Scheduling and shortcut resistance

The default source quadrant cycles with period 4. The cross offset cycles through all nine ordered pairs in `{-1,0,1}²`. Because 4 and 9 are coprime, every quadrant is paired with every cross offset over 36 examples. Shape sizes and dimensions vary by difficulty while canonical 9/11/13 profiles remain frequent.

A first repaired draft (2.0) accidentally correlated each quadrant with one cross offset. A self-review test proved that a quadrant-to-offset lookup could ignore the visible cross. Version 2.1 replaced that schedule with the full 9-pair cycle and added the lookup as a second executable rival. The retained red tests are under `checks/task-tests-quadrant-red/`; the final green suite is under `checks/task-tests-final-v21/`.

Declared canonical-fitting rivals:

- `assume_centered_cross`: reflect around the geometric canvas center rather than the visible color-9 cross.
- `assume_quadrant_offset_schedule`: infer off-center axes from the source quadrant using the retired 2.0 correlation.

Both fit all five canonical pairs. Generated off-center/cross-decoupled cases refute them, and `lesson_identifiable` rejects a lesson when a declared competitor survives the demonstrations but changes the query.

## Final measured evidence

- Task-local wrapped tests: 57 passed, including live Racket parity.
- Semantic gate: 600/600 strict-valid cases; 2/2 witnesses; 2/2 rival claims; 12/12 lesson samples identifiable.
- Source-bound lesson census: 300/300 four-demo lessons unambiguous; 100 per band; 1,500 pair occurrences; 1,391 exact unique inputs; both logical rivals refuted in every lesson.
- Independent probe: 250 draws per band, zero invalid or nondeterministic cases; all nine offset pairs for each quadrant; live Racket parity 70/70.
- Racket authority and canonical data are unchanged.

See `workspace/reference_probe.py` for the independent oracle, rival implementations, joint-support census, and Racket parity batch. See the packet-root `REVIEW.md`, `DECISIONS.md`, and `QUESTION_ANSWER.md` for the complete handoff.
## Current reviewer considerations

Source SHA-256: `5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca`.

# Decisions: generator 77871cecd343

All final measurements below bind to generator SHA-256 `5e1fdbc628e7c565974c9cfeacef0d6fbe5b412ce9ab23a6f45a94ffe4ff0aca`, version `2.1.0`, and unchanged canonical rule hash `1bad9bf6a465`.

## D1 — Treat the Racket program as unchanged label authority

**Choice.** Repair only the Python input sampler, validator, tests, and evidence. Do not change the selected Racket source or canonical puzzle row.

**Why.** The live rule already transformed every canonical example and 120 baseline generated inputs without crash. The defect was distributional and contractual: the baseline generator did not represent the canonical input grammar. Authority sync now reports synchronized source and execution parity.

**Rejected alternative.** Rewriting the Racket program to fit the narrow baseline would codify the generator defect and break canonical examples.

**Evidence/failure mode.** Final authority and canonical hashes equal the packet baseline. The Racket linter has two nonblocking `style-not-eq` advisories but zero errors; no semantic authority change was justified.

## D2 — Generate one explicit full color-9 cross

**Choice.** Inputs contain exactly one complete color-9 row and one complete color-9 column. Default axes are at geometric center plus independent row/column offsets in `{-1,0,1}`.

**Why.** The visible cross is the task's operative coordinate system. Moving it creates the decisive counterexample to the strongest canonical shortcut, which uses the canvas center.

**Alternatives rejected.** Center-only axes preserve canonical appearance but never distinguish cross detection from center memorization. Larger offsets were not chosen because they reduce usable quadrant area on canonical-size boards and are not needed to identify the rule.

**Controls and limits.** `row_offset` and `col_offset` are exact observable controls. `self_check` rejects axes outside ±1. This is a deliberate training domain, not a claim that the Racket rule is undefined for farther offsets.

## D3 — Decouple cross offset from source quadrant

**Choice.** Cycle source quadrant with period 4 and joint cross offset with period 9 over all ordered pairs in `{-1,0,1}²`. Since the periods are coprime, each quadrant receives every offset pair over 36 consecutive samples.

**Why.** Version 2.0 paired each quadrant with one offset. A lookup rival could infer the axis from the quadrant and ignore the cross. The retained red test `checks/task-tests-quadrant-red/` exposed this second-order shortcut.

**Alternatives rejected.** Independent random draws could leave short lessons without coverage. Four hand-selected quadrant/offset pairs guarantee local diversity but create the exact correlation that failed self-review. The 4×9 deterministic product gives reproducible full support and keeps every four-example window quadrant-complete.

**Evidence.** The final task test checks all 36 joint states. The independent 250-per-band probe found all nine offset pairs under every quadrant; the retired lookup rival disagreed on 202/250 cases in each band.

## D4 — Use all four source quadrants

**Choice.** `source_quadrant` cycles through `top_left`, `top_right`, `bottom_left`, and `bottom_right`; every four consecutive examples contain all four.

**Why.** Three of five canonical inputs contradict the baseline's upper-left-only assumption. Quadrant-complete lessons prevent a solver from treating a particular side as fixed and expose horizontal, vertical, and double reflection symmetrically.

**Alternatives rejected.** Upper-left-only generation was the central baseline defect. Random quadrant selection does not guarantee four-demo lesson coverage.

**Limit.** The source occupies exactly one quadrant and never crosses the axes. Interaction between source cells and the cross is intentionally excluded because the authority's copy behavior there is not identified by the canonical task.

## D5 — Generate one exact-size 4-connected source shape of 3–8 cells

**Choice.** Grow an exact-size 4-neighbor connected set inside the chosen quadrant. Easy uses 3–5 cells, medium 4–6, hard 6–8; exact overrides allow 3–8.

**Why.** Canonical sources are connected shapes, including 4- and 5-cell examples rejected by the baseline. Connectivity preserves an object-level task rather than a bag of independent points, while size variation tests reflection of nontrivial geometry.

**Alternatives rejected.** Isolated random cells reproduced the baseline shortcut. Arbitrary disconnected sets introduce a different multi-object grammar. Shapes larger than 8 add crowding without a new semantic distinction on 9×9 boards.

**Failure handling.** Construction uses the maximal symmetric source region around the cross, so all reflections remain in bounds and initially background. Overrides that cannot satisfy advertised constraints are rejected rather than silently changed.

## D6 — Use 9–15 dimensions with canonical-heavy deterministic profiles

**Choice.** Exact `grid_h`/`grid_w` controls accept 9–15. Defaults use difficulty-specific profiles dominated by 9, 11, and 13, with 15 appearing in hard.

**Why.** Canonical-like sizes keep profile support while rectangular and larger boards prevent memorizing one shape. The cross geometry, not canvas dimensions, controls the transformation.

**Alternatives rejected.** Fixed 8×8 baseline boards missed canonical profiles and constrained shape support. Very large boards would inflate compute and sparsity without teaching a new rule.

**Evidence.** Profile floor accepts all 5 canonical inputs and reports 34/60 exact-profile plus 42/60 envelope hits. Final diversity reports six input/output shapes.

## D7 — Advertise only six exact, pixel-observable controls

**Choice.** `AXES` contains only `grid_h`, `grid_w`, `row_offset`, `col_offset`, `source_quadrant`, and `shape_cells`. Unknown keys and invalid values raise `ValueError`; `observe_overrides` recovers all six from the returned grid.

**Why.** The baseline declared dead/singleton axes, ignored textures, accepted unknown keys, and failed thousands of override probes. An exact control is useful only when it changes and can be observed in output pixels.

**Alternatives rejected.** Keeping decorative `palette_size`, `density`, `position_bias`, or texture axes would preserve a misleading API. No incompatible combinations are needed within the final declared domains.

**Evidence.** Override gate passes 35,910/35,910 accepted draws across 399 cases and three bands, with zero explicit combination rejection.

## D8 — Remove textures entirely

**Choice.** `HELPFUL_TEXTURES` and `DEGENERATE_TEXTURES` are empty.

**Why.** The task input has a precise three-color structural grammar. Baseline “helpful” textures were byte-identical to default, and degenerate fixtures leaked into the ordinary valid domain.

**Alternatives rejected.** Adding noise or palette variants would either alter the task semantics or create nuisance variation not supported by the canonical rule.

## D9 — Validate the complete advertised input grammar

**Choice.** `self_check`/`strict_canonical_like` require: rectangular ARC grid; size 9–15; colors subset `{0,1,9}`; one full 9-row and 9-column; offsets ±1; 3–8 color-1 cells; one quadrant; 4-connectivity; and distinct, in-bounds, initially background reflections.

**Why.** A validator must accept all lawful generated/canonical inputs and reject malformed examples that erase the semantic signal.

**Evidence.** Final self-check is clean on 60 generated inputs, accepts 5/5 canonical inputs, and rejects 66/66 destructive mutations. Task-local tests add malformed-grid and targeted mutation cases.

**Limit.** The validator describes the selected training domain, not every grid on which the general Racket program could execute.

## D10 — Declare executable canonical-fitting rivals and witnesses

**Choice.** Declare two logical rivals in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`: geometric-center axes and retired quadrant-to-offset lookup. Pair them with `off_center_cross` and `off_quadrant_schedule` witnesses. `lesson_identifiable` checks all declared competitors.

**Why.** Both rivals fit every canonical pair, so ordinary canonical parity cannot distinguish them. Executable rivals make the training claim falsifiable.

**Alternatives rejected.** A prose-only warning cannot be checked by gates. Declaring only the centered rival missed the correlation introduced by the first repair.

**Evidence.** Semantic gate: strict 600/600, witnesses 2/2, rival claims 2/2, lesson sample 12/12. Source-bound census: 300/300 lessons unambiguous; each two logical rivals refuted in every lesson.

## D11 — Require four demonstrations per lesson

**Choice.** `EXAMPLES_NEEDED = 4`; every four consecutive scheduled examples cover all quadrants and refute both declared competitors.

**Why.** Four is the smallest deterministic window that can show each quadrant once. The schedule makes rival refutation a lesson-level property rather than relying on aggregate witness frequency.

**Alternatives rejected.** Fewer than four examples cannot guarantee all quadrants. More examples add cost without a demonstrated identifiability benefit.

**Limit.** The census samples four demos plus one query from production assembly and does not prove universal induction or enumerate undeclared rivals. It reports exact-grid uniqueness, not semantic equivalence classes.

## D12 — Add independent probes rather than trusting generator helpers

**Choice.** `workspace/reference_probe.py` implements its own cross detector, intended reflection, centered rival, quadrant-offset rival, support census, and Racket parity batch.

**Why.** Testing a helper with itself can preserve the same bug on both sides. Independent coordinate code and live authority comparison provide a separate failure surface.

**Evidence.** Across 250 cases per band: zero invalid, zero nondeterministic, all outputs changed, exact unique inputs 238/240/239, centered rival disagreement 222/250 per band, quadrant rival disagreement 202/250 per band, and Racket parity 70/70.

## D13 — Preserve failed iterations and scope audit findings

**Choice.** Keep baseline failures, red TDD runs, the invalidated 2.0 solve under `checks/prior-solve/`, interrupted aggregate receipts, and both assigned audit counterexamples. Do not modify audit-target generators.

**Why.** These records show what each test can catch and prevent a later agent from mistaking a superseded pass for final evidence.

**Limit.** Successful high-volume per-draw traces may be pruned from the return to meet the 25 MiB expanded evidence budget; decisive summaries, source-bound lesson materialization, failures, and counterexamples remain.
