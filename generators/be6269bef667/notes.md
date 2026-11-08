# Working notes: `be6269bef667`

## Current rule and authority

Colors `1/2/3/4` emit rays up/right/down/left. A ray includes its emitter, passes through other emitters, stops before color `5` or the boundary, and adds one to a fresh count grid. The canonical Racket source was not changed. `RULE_HASH = "c3e717030acc"`.

Final generator version: `3.0.0`; SHA-256 `48d327986948b9ee31cbd0dcfeb8d8381ed0ce016efc4bfacc50f3393122e9d8`.

## Reversed baseline decisions

The baseline advertised many palette, texture, density, and position controls that were singleton, ignored, or semantically unsafe. It also accepted malformed scalars and unknown overrides. That contract was replaced rather than patched: the only public axes are exact integer `grid_h` 7–10, `grid_w` 8–10, `n_emitters` 7–10, and `n_walls` 4–6. `observe_overrides` recovers all four from pixels.

Random independent placement was replaced by constructive geometry. Every production input has all four directions, an overlap, a wall/emitter interaction, and a downward emitter blocked by a wall with cells beyond it. Extra objects remain randomized without cutting the protected witness paths.

## Strongest shortcut and curriculum decision

All five canonical labelled pairs fit `downward_ignores_walls`: direction 3 continues through color 5 while other directions stop. The minimized Racket-checked counterexample is `counterexamples/downward-wall-shortcut.json`. The sampler now emits a refuting `downward_wall_stop` witness in every draw and declares the rival through the semantic and lesson contracts.

Lessons use 3 demonstrations and 1 query. Arbitrary query positions are supported: the final census materialized 300 lessons and checked all 1,200 holdouts with 0 ambiguities against declared rivals.

## Validation boundary

`self_check` accepts lawful canonical-compatible inputs: rectangular 7–10×8–10 grids, colors 0–5, 7–10 emitters, 4–6 walls, every direction, overlap, and at least one wall/emitter interaction. It deliberately does **not** require the downward-wall witness because canonical inputs lack that branch. `generate` separately guarantees the stronger production witness.

## Tests and tools

Portable tests live in `tests/test_generator.py`; final task-test result is 54 passed, 1 intentional `None`-override skip. `workspace/reference_probe.py` independently checks canonical oracle agreement, determinism, exact witness frequency, rival disagreement, unique inputs/shapes, and optional real-Racket parity. The 1,000-draw retained probe had no validator or determinism failures and refuted the rival in every draw.

## Known limits / open findings

No selected-task blocker remains. Evidence is finite and only rules out declared plus bounded searched rivals; it is not a proof of unique induction. The production distribution is intentionally constrained to task-defined colors and canonical-compatible dimensions/counts. The archival bank `raw_code` is textually divergent from the selected/canonical rule but passed execution-parity authority checks and was not modified.

No prior associated review was used as a lead; `evidence/associated_notes.jsonl` was empty for this assignment.
## Current reviewer considerations

Source SHA-256: `48d327986948b9ee31cbd0dcfeb8d8381ed0ce016efc4bfacc50f3393122e9d8`.

# Decisions for `be6269bef667`

Final generator SHA-256: `48d327986948b9ee31cbd0dcfeb8d8381ed0ce016efc4bfacc50f3393122e9d8`.

## D1 — Preserve the canonical Racket authority

**Choice.** Do not change the Racket rule or canonical ledger; pin `RULE_HASH = "c3e717030acc"`.

**Rationale.** The canonical program correctly implements the intended directional-ray count map, and an independent Python interpreter matched all five canonical pairs. The defect was in input generation, validation, and teaching coverage, not label authority.

**Alternatives considered.** Rewriting the rule to simplify testing was rejected because it would widen review scope without fixing the generator contract. Treating the divergent archival `raw_code` as selected authority was also rejected; the selected task rule and canonical program are exact matches, while the after battery’s authority check confirmed execution parity for retained authority texts.

**Evidence.** `checks/after/checks/be6269bef667_after_battery_summary.json`; `checks/be6269bef667-reference-probe.json`.

**Limit.** The archival raw source remains textually divergent. It is not selected by this task and was left unchanged.

## D2 — Replace the advertised axis set instead of emulating fictitious controls

**Prior choice.** Version 2.x advertised dimensions, counts, palette/texture controls, singleton color-count metadata, density, and position bias. Many values were ignored or impossible to observe, and unknown keys were accepted.

**New choice.** Expose exactly four integer axes recoverable from returned pixels: `grid_h`, `grid_w`, `n_emitters`, and `n_walls`.

**Rationale.** An override contract should describe causal controls, not taxonomy. The four retained values are independently drawable, exactly enforceable, and recoverable with `observe_overrides`. Removing dead palette/texture aliases is safer than inventing color substitutions for task-defined direction symbols.

**Alternatives considered.** Implementing all legacy metadata was rejected because palette swaps would change semantic symbols and singleton axes cannot demonstrate an effect. Marking ignored axes diagnostic was rejected because callers had no useful diagnostic behavior to observe.

**Probe/failure mode.** The baseline override checker recorded 48,811 findings over 55,890 draws; the final checker exercised 90 cases and 8,100 accepted draws with zero findings or warnings and rejected the unknown-key probe.

**Evidence.** `checks/before-override/checks/be6269bef667_before_override_results.json`; `checks/after/checks/be6269bef667_after_override_results.json`.

## D3 — Use canonical-compatible dimensions and object counts

**Choice.** Generate 7–10 rows, 8–10 columns, 7–10 emitters, and 4–6 walls. Weight 7/8-row and 8/9-column profiles toward canonical support while retaining every advertised value.

**Rationale.** The baseline generated larger sparse grids and missed every canonical profile in the 60-draw floor. These ranges include all five canonical inputs, leave enough cells for protected interactions, and keep exact overrides constructive across the full Cartesian domain.

**Alternatives considered.** Exact replay of the three observed canonical profiles was rejected as overfitting and low-diversity. Wider legacy ranges were rejected because they weakened canonical support without teaching additional rule branches.

**Probe/failure mode.** Too-small grids can make the wall witness or crossing anchors collide; therefore the minimum is 7×8. Too many walls could exhaust safe cells or cut protected paths; the maximum remains six.

**Evidence.** `checks/after/checks/be6269bef667_after_profile_floor.json`; `checks/after/checks/be6269bef667_after_override_results.json`.

## D4 — Construct interactions rather than hope random placement creates them

**Choice.** Place four semantic anchors first: a downward emitter at the top, an upward emitter at the bottom of the same column, opposing horizontal emitters on a variable crossing row, and a wall between the vertical emitters. Add remaining walls off the protected row/column, then add remaining emitters.

**Rationale.** The transformation is about ray propagation, blocking, and additive overlap. Independent random placement can produce valid-looking grids with no wall interaction, no overlap, or no evidence that rays pass through symbols. Constructive anchors guarantee the branches while keyed random choices vary geometry.

**Alternatives considered.** Rejection sampling was rejected because it makes override coverage and runtime unpredictable. Fixed templates were rejected because they create an obvious positional shortcut. Purely random objects plus a weak validator was the baseline failure.

**Probe/failure mode.** A fixed witness column or row would leak the answer. The geometry RNG varies witness column, crossing row, wall row, and left/right edge positions. Across 1,000 independent draws, each mode produced 250 unique inputs and 11 shapes.

**Evidence.** `checks/be6269bef667-reference-probe.json`; `repo/generators/be6269bef667/workspace/reference_probe.py`.

## D5 — Teach the strongest canonical-fitting shortcut explicitly

**Choice.** Declare `downward_ignores_walls` as the canonical shortcut/lesson competitor and require a `downward_wall_stop` witness in every production draw.

**Rationale.** All five canonical labelled pairs are compatible with a rule that checks walls for directions 1, 2, and 4 but not direction 3. This is more plausible and more task-specific than generic identity/flip rivals because the demonstrations simply never place a wall below a downward emitter.

**Alternatives considered.** A generic “walls never block” rival is already contradicted by canonical pairs and therefore is weaker as a curriculum target. Randomly emitting the witness was rejected because a lesson could contain no refuting demonstration.

**Probe/failure mode.** The minimized 7×8 counterexample differs in five cells. The supported Racket apply command, independent Python oracle, 600-draw semantic gate, and 1,000-draw probe agree. Every 3-demo lesson therefore contains multiple refutations, making any one query holdout safe.

**Evidence.** `repo/generators/be6269bef667/counterexamples/downward-wall-shortcut.json`; `checks/be6269bef667-counterexample/racket.json`; `checks/after-semantic_gate-1/checks/be6269bef667_after_semantic_gate.json`; `checks/lesson-census-final.json`.

## D6 — Separate lawful-input validation from production teaching guarantees

**Choice.** `self_check`/`strict_canonical_like` validate rectangular 7–10×8–10 inputs, colors 0–5, 7–10 emitters, 4–6 walls, every direction, overlap, and at least one wall/emitter interaction. The production sampler additionally enforces `_has_downward_wall_stop`.

**Rationale.** Requiring the new witness in `self_check` would reject canonical inputs—the very evidence the generator must remain compatible with. The validator therefore captures the lawful task manifold, while `generate` captures the stronger curriculum policy.

**Alternatives considered.** A shape/palette-only validator was rejected as toothless. A witness-mandatory validator was rejected as canonical-incompatible.

**Probe/failure mode.** Focused destructive-mutation tests cover missing directions, invalid colors/counts, absent overlap, and absent interactions. The strict semantic census measured 600/600 accepted generated draws and 0/5 canonical rejections.

**Evidence.** `repo/generators/be6269bef667/tests/test_generator.py`; `checks/after-semantic_gate-1/checks/be6269bef667_after_semantic_gate.json`.

## D7 — Reject malformed calls at the source

**Choice.** Require `seed` and nonnegative `sample_index` to be actual integers (not booleans); reject unknown axes and non-integer/out-of-range overrides. Preserve `None` as the framework’s explicit “no override” convention.

**Rationale.** Silent coercion and ignored unknown keys made reproducibility receipts misleading. Early errors make an invalid call distinguishable from a sampled puzzle.

**Alternatives considered.** Coercing numeric strings/floats was rejected because it changes the keyed-RNG identity and obscures caller bugs.

**Evidence.** `repo/generators/be6269bef667/tests/test_generator.py`; `checks/after/checks/be6269bef667_after_defect_lint.log`; `checks/after/checks/be6269bef667_after_override_results.json`.

## D8 — Require arbitrary query rotations for the retained lesson policy

**Choice.** Retain `EXAMPLES_NEEDED = 3`, assemble three demonstrations and one query, and require every one of the four labelled positions to remain identifiable when held out.

**Rationale.** The intended downstream policy does not rely on a privileged query position. Because every sampled pair contains the downward-wall witness, the declared rival is refuted by any remaining demonstration after rotation.

**Alternatives considered.** An ordered-only curriculum was unnecessary and would add a hidden assembly dependency. Declaring a cyclic schedule period was rejected because the sampler is stateless and has no finite lesson schedule to enumerate.

**Evidence.** Required semantic smoke: 12 lessons and 48 rotations, all identifiable. Large census: 300 lessons, 1,200 rotations, 0 ambiguities (`checks/lesson-census-final.json`).

**Limit.** These are finite checks against declared and bounded searched rivals, not a proof of unique human induction.

## D9 — Add task-local reusable tooling, not shared-code changes

**Choice.** Add `workspace/reference_probe.py`, a standalone source-bound audit that independently interprets rays, checks canonical data, samples each difficulty mode, and optionally invokes the real Racket authority.

**Rationale.** Future agents need a quick way to distinguish Python-mirror observations from authority parity and to reproduce the exact semantic witness without private imports.

**Alternatives considered.** Editing shared reviewer tools was unnecessary for this task and outside the selected-task delta. Copying a full staged runtime into the return was rejected; only the small probe and decisive JSON receipts are retained.

**Evidence.** `checks/be6269bef667-reference-probe.json`; `repo/generators/be6269bef667/workspace/reference_probe.py`.

## Review review-e1bae10251bf9386 — native parametric family

A matched-input two-setting family was added under `workspace/parametric/` without changing the production generator or selected canonical authority.

- `weighting=unit` returns the exact canonical Racket source byte-for-byte and adds one along every directed ray.
- `weighting=plurality_double` first counts emitters by direction, derives the unique plurality direction from the input, and then traces all rays with weight two for the selected direction and one for the other three.
- The sampler supports 2–6 prefix-stable demonstrations and 1–4 prefix-stable queries. Its query shapes are 10×13, 17×19, 30×30, and 24×29; the 30×30 case uses 33 nonzero input cells and yields about 490 nonzero output cells while retaining walls, all four directions, boundary contact, and bounded overlap.
- The minimum lesson changes the plurality direction, and a ten-rival bank covers unit, fixed-direction weighting, least-direction weighting, selected-only, nonselected weighting, and count-proportional weighting.

The first stress profile was semantically valid but covered only 383–396 output cells, below the retained large-case threshold. Increasing the edge-emitter counts while reducing nonessential walls preserved the rule branches and raised observed coverage to 490–496 cells without increasing the maximum output value beyond three. Final bounded evidence covers 192 episodes, 24 protected-Racket parity evaluations, and zero surviving named rivals. This is finite evidence, not a claim of universal identifiability or training benefit.
