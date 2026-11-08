# b0e266482663 — crossing rays with blockers

Version `4.6.0`; generator SHA-256 `bd9bba5d02cec811f5e7a6f9b209281bfe604f47f224d9598e2bc050476e23ec`; unchanged canonical rule hash `d12310adc715`.

A zero-background grid has green (`3`) column shooters on the top edge and red (`2`) row shooters on the left edge. Red rays travel right, green rays travel down, and interior maroon (`9`) cells stop them. A cell reached only horizontally becomes `2`, only vertically becomes `3`, and by both rays becomes cyan (`8`). Blockers remain `9` and untouched cells remain unchanged.

## Training distribution

Generation is constructive rather than rejection-based. Every ordinary draw contains:

- at least one visibly causal horizontal blocker and one visibly causal vertical blocker, each with a non-blocker background cell beyond it;
- at least one horizontal-only fill, vertical-only fill, and cyan crossing;
- shooters and blockers at varied coordinates inside a coherent source-like or controlled-generalization shape;
- exact agreement with the unchanged input-pure rule mirror and the public realized axes.

Three deterministic schedule profiles form each three-example lesson:

1. `adjacent_first_step` demonstrates adjacent border origins and immediate stops on both axes;
2. `separated_stops` demonstrates at least two productive shooters per axis and a cyan crossing not confined to the lowest row/column shooters;
3. `late_stops` reaches the public maximum of four productive shooters per axis and visibly stops both the lowest and highest shooter on each axis.

Because `EXAMPLES_NEEDED = 3`, every three consecutive default examples contain all three profiles. The final lesson contract has 16 semantic witnesses and 24 declared rivals. It explicitly falsifies fixed first/last one-, two-, and three-marker emission caps, crossing-color shortcuts tied to the lowest shooters, and blocker semantics that apply only to a marker subset.

## Public controls

The observable axes are `grid_h` (`6..13`), `grid_w` (`6..14`), `n_row_shoot` (`1..4`), `n_col_shoot` (`1..4`), and `n_blockers` (`2..10`). Unknown keys are rejected. `observe_overrides()` recovers the realized values, and generation verifies them before returning. Exact low-count overrides remain lawful grid controls; the full three-profile curriculum guarantees apply to defaults.

## Measured coverage

The version-6 probe ran 500 deterministic draws per difficulty. In every band, all 500 draws had both visible stop directions, all three output branches, deterministic replay, and no `self_check()` failure. Unique inputs were 484 easy, 492 medium, and 500 hard. Canonical shapes appeared in 372, 377, and 389 draws. The maximum-cardinality fixture appeared in 167, 172, and 188 draws; the probe observed both extreme row stops in 184/189/224 and both extreme column stops in 179/195/220 easy/medium/hard draws. All 36 tested three-demonstration windows were lesson-identifiable, and the probe's independent 18-shortcut census refuted every shortcut in every tested window.

Four larger independent probes checked 3,000 lesson windows per band. Every tested fixed-cardinality, crossing-color, global-wall, and marker-specific blocker-scope rival was refuted in `3000/3000` windows for easy, medium, and hard. A separate sweep checked 60,000 defaults plus the complete declared override cross-product once per schedule profile—91,104 generations total—with zero failures.

The reusable tools and final evidence are `workspace/distribution_probe.py`, `workspace/distribution_after.json`, and `workspace/visibility_override_sweep.json`.

## Intentional limits

The structured late fixture trades some sampled uniqueness for semantic certainty, especially in easy and medium. Shape sampling remains source-weighted rather than uniform over all legal dimensions. The rival set is broad but not a proof against every possible program, so downstream filtering or reordering should rerun `lesson_identifiable()` and the independent shortcut probe on the examples actually used.
