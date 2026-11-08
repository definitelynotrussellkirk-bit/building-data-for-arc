# Working notes: 364829da8490

## Current intended rule

Treat each 4-connected color-0 region independently. Fill it exactly when it does not touch the canvas border and all cardinally adjacent nonzero cells have one color; use that local color. Exterior/open regions and enclosed regions with mixed cardinal boundary colors remain zero. The selected canonical Racket authority remains unchanged at rule hash `c1200d217d20`.

## Current generator design

Version `3.0.0`, final reviewed SHA-256 `9e959ee0403be69176f40294a4bdd93f0bddfccd74f1c92f9da570f1ab10f3c6`.

- Four profiles: `rect_pair`, `open_vs_closed`, `mixed_border`, `irregular_hole`.
- Eight-pair deterministic cycle: every profile appears twice.
- Seven demonstrations plus one query; any query holdout leaves all four profiles in the demonstrations.
- Exact axes `grid_h`, `grid_w`, and `scene_profile` are validated before `GenCtx` coercion.
- Twelve declared semantic rivals are scored by `lesson_identifiable` and the public census.

## Prior lead used

I used retained audit `review-535f1f762a14ec62:v0001` only as a lead. Its source-bound findings were against baseline SHA-256 `28e22a781143e90ee50e0cadee2054296b6f99ac0e2b1ddf6f67f1186afe4a4a`: fractional integer controls were silently truncated, and a lawful missing-corner mutation distinguished four- from eight-connected zero regions while fitting sampled teaching support. The retained source is indexed in `evidence/review_index.json` and under `counterexamples/review-535f1f762a14ec62-v0001/`.

## Decisions and reversals

1. **Pre-coercion validation.** Reject malformed, noninteger, out-of-range, unknown-axis, and unknown-profile requests before drawing.
2. **Topology witnesses.** Open-vs-closed tests zero-region border contact and four-connectivity; mixed-border includes a disconnected one-cell enclosure; irregular-hole makes a foreign color diagonal-only.
3. **Schedule reversal.** An initial five-demo/three-profile repair was rejected because the immutable frozen fixture required the full four-profile curriculum. The final eight-pair cycle repeats every profile twice.
4. **Palette-floor reversal.** The first topology repair hit the canonical size/palette envelope only 9/60 times. A second color is now buried in a solid closed-wall block so the palette matches the canonical envelope without changing any zero-region boundary.
5. **Frozen fixture preserved.** `tests/test_generator_364829da8490.py` remains unchanged; new regressions live in `tests/test_review_20261008.py`.

## Final evidence

- Strict battery: 12/12 green in `checks/after-final/`.
- Focused final task tests: 27/27.
- Production census: 300 lessons, 2,400 rotations, 0 ambiguities, 2,334 unique inputs; summary and compressed lossless report under `checks/lesson-census-final.*`.
- Schedule census: 24 band/start lessons and 192 rotations, 0 ambiguities, in `checks/schedule-census-final.json`.
- Racket-bound topology counterexamples: `counterexamples/review-4f992a677197c2e1-v0001/`.
- Reusable mirror probe: `workspace/probe_topology_curriculum.py`.

## Known limits and open findings

This is a calibrated four-profile teaching grammar, not an exhaustive enumerator of every enclosing topology. The finite 12-rival pass does not prove uniqueness against undeclared programs. The seven-demonstration contract is deliberately longer than the baseline. No local blocker remains, but promotion should still use the normal independent monitor on the exact returned SHA.
## Current reviewer considerations

Source SHA-256: `9e959ee0403be69176f40294a4bdd93f0bddfccd74f1c92f9da570f1ab10f3c6`.

# Decisions for `364829da8490`

## D1 — Keep the canonical rule unchanged

**Choice.** Preserve canonical Racket rule hash `c1200d217d20` and repair only the generated input distribution, controls, lesson contract, tests, and reviewer tooling.

**Rationale.** The prior audit supplied a lawful accepted-domain grid on which the selected Racket rule clearly distinguishes four- from eight-connectivity. The defect was absent teaching support, not an incorrect authority. Three final generated counterexamples were labelled through public Racket apply and matched the independent Python mirror.

**Alternative rejected.** Narrowing the validator to exclude the diagonal-connectivity witness would hide a real rule distinction and contradict the task's topological semantics.

**Evidence.** `checks/main-counterexamples/witnesses.json`; `checks/main-counterexamples/racket.json`.

## D2 — Validate exact controls before `GenCtx` coercion

**Choice.** Reject booleans, strings, fractional numbers, out-of-range dimensions, nonstring profiles, unknown profiles, and unknown axes before constructing `GenCtx`.

**Rationale.** The baseline accepted `grid_h=16.9` as 16. Exact controls are an API contract; silently changing a caller request produces mislabeled metadata even when the resulting grid is lawful.

**Alternative rejected.** Checking only the realized grid after generation cannot recover the caller's uncoerced value once the converted value has replaced it.

**Failure mode/limit.** This validates the three declared axes only; future axes must be added to the same pre-coercion contract.

## D3 — Use four diagnostic profiles, each twice, in an eight-pair cycle

**Choice.** Set `EXAMPLES_NEEDED = 7`, `SCHEDULE_PROFILES = SCENE_PROFILES + SCENE_PROFILES`, and `LESSON_SCHEDULE_PERIOD = 8`.

**Rationale.** Any one held-out pair leaves seven demonstrations containing every profile at least once. That makes the actual exported lesson rotation-safe rather than relying on favorable query placement.

**Reversal.** The first repair used a shorter five-demo schedule with three required profiles. It failed the immutable frozen curriculum test because the baseline contract still required `rect_pair`. Rather than modifying the frozen fixture, I restored it and adopted the eight-pair cycle.

**Alternative rejected.** A four-pair cycle covers each profile only once; holding out one pair removes the sole witness for that profile. Random resampling would not prove coverage in every complete lesson.

**Cost/limit.** Lessons are longer: seven demonstrations and one query. The schedule proves coverage for declared deterministic profiles, not all seeds or all conceivable rivals.

## D4 — Make topology distinctions observable with compact witnesses

**Open-vs-closed profile.** Remove a frame corner so the interior connects to exterior only under eight-connectivity. Use the same wall color on open and closed shapes so a rule that ignores border contact also makes a visible error.

**Mixed profile.** Enclose a one-cell hole with four disconnected cardinal wall cells. This refutes both “boundary wall cells must be connected” and “single-cell holes are ignored.” A separate mixed-color enclosure remains unchanged as a negative control.

**Irregular profile.** Put a different color on a frame corner that touches the fillable zero region only diagonally. This isolates cardinal from eight-neighbor boundary-color collection.

**Alternative rejected.** Merely declaring rivals without guaranteed per-lesson witnesses would allow the semantic census to pass individual draws while still yielding ambiguous held-out queries.

**Evidence.** `generators/364829da8490/tests/test_review_20261008.py`; `checks/main-counterexamples/witnesses.json`.

## D5 — Preserve canonical size/palette support without corrupting the witness

**Choice.** In `open_vs_closed`, place a second color inside a solid block attached to the closed wall, where it is not cardinally adjacent to any zero cell.

**Reversal.** The first topology repair passed focused semantic tests but the strict battery found only 9/60 canonical-envelope hits (15%), below the required floor. The added buried color restored a three-color palette while leaving all zero-region decisions unchanged.

**Alternative rejected.** Putting the second color on a wall boundary would change the intended one-color boundary into a mixed-color negative, destroying the topology witness.

**Final evidence.** `checks/after-final/checks/364829da8490_after_profile_floor.json`: 19 exact and 24 envelope hits among 60 draws, with exact hits in every band.

## D6 — Declare and score the plausible rivals that motivated the repair

Added rivals:

- `ignore_border_contact`
- `use_eight_connected_zero_regions`
- `use_eight_neighbor_boundary_colors`
- `require_connected_boundary`
- `skip_single_cell_holes`

They join the seven existing rivals for 12 declared competitors. `lesson_identifiable` also requires all four teaching profiles in demonstrations. The large census iterates the generator's actual declarations; no external copied rival-name list is used as authority.

**Limit.** A finite rival pass is evidence against those 12 implementations, not a proof of unique induction. Structured profile geometry may still support an undeclared shortcut.

## D7 — Retain full evidence compactly

The 300-lesson report is about 23 MB uncompressed. It is retained losslessly as `checks/lesson-census-final.json.gz`; `checks/lesson-census-final.manifest.json` records the original path, byte count, SHA-256, compressed SHA-256, and exact restoration command. A small summary supports one-minute intake without discarding the full instances.
