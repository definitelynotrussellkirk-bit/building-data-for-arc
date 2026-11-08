# Working notes: 9d52c9d09009

## Rule and authority

The selected rule finds each 4-connected color-8 object, restricts attention to its tight bounding box, counts 4-connected zero regions in that box, and recolors the object's 8-cells by the count, except `4 -> 7`. Zeros and unrelated colors are preserved. The canonical rule hash remains `3d808db30609`; this review did not change the Racket semantics.

The base authority's selected `target_code` was synchronized to the exact canonical text. Its archival `raw_code` remains unchanged and intentionally differs textually. The final generator SHA-256 is `1454bbd932334cd47503de4be8d3ff4b906db587b75416bca60d53475224efb6`.

## Baseline defects reproduced

The before battery was 8 green, 2 advisory, and 2 failed. It showed:

- non-literal scalar values accepted for `seed` and `sample_index`;
- no executable semantic witness/rival contract;
- exact canonical-size support absent from medium and hard default draws;
- selected authority text not exact-canonical even though execution parity held.

## Distribution and lesson decisions

Public profiles retain the four official object-family morphologies while varying placement and nuisance layout on the corresponding canonical canvas dimensions in every difficulty band. General profiles retain the same counting rule but include diagonal zero contacts that are separate under 4-connectivity and merged under 8-connectivity.

The production schedule has declared period two: even sample indices select public-family scenes and odd sample indices select generalized scenes. A lesson contains three demonstrations and one query. This deterministic alternation was chosen instead of an unconstrained random mixture because a random four-pair window can contain no rival-refuting example. Exact `scene_profile` overrides bypass the schedule.

The strongest canonical-fitting rival is `eight_connected_zero_regions`. It fits all four canonical pairs. The minimal retained witness is:

```text
8 8 8 8
8 0 8 8
8 8 0 8
8 8 8 8
```

The intended rule counts two 4-connected zero regions and recolors the object `2`; the rival merges the diagonally touching zeros and recolors it `1`. The canonical Racket runtime confirmed the intended output. Evidence is retained in `counterexamples/four-vs-eight-connectivity.json` and `checks/shortcut-witness/`.

## Verification

The strict final battery is 12/12 green with required query rotations. Its semantic gate accepted 600/600 sampled inputs, all 4 canonical inputs, fired the connectivity witness on 315/600 samples, verified the declared rival claim, and found 0 ambiguous query rotations out of 48.

A fixed-seed exhaustive enumeration covered both declared schedule-start residues in all three bands: 6/6 lessons and 24/24 query rotations were identifiable against the rival. A wider census materialized 300 lessons (100 per band), 1,200 exact-unique inputs, and 1,200 held-out-query rotations with zero detected ambiguity or scoring/materialization errors. These are finite declared-rival checks, not a proof against every possible hypothesis.

Twenty-six new focused portable tests pass. The aggregate `task_tests` stage remains blocked before pytest by the inherited frozen root fixture's fixed-depth canonical path. That fixture was not modified, per packet policy; the maintainer owns its future migration.

## Parametric prototype

`workspace/parametric/prototype.py` proposes one episode-level parameter, `four_region_color in {4, 7}`, selected once and held fixed across three demonstrations and one query. The canonical default `7` returns the exact canonical Racket program; setting `4` narrowly changes only the four-region output mapping. Two retained Racket-backed episodes show all demonstrations distinguish the settings and both queries differ. This is a prototype only and is not wired into production generation or approved for training/export.

## Remaining limits

- The semantic contract tests one named plausible rival plus shared generic rivals; it cannot establish universal identifiability.
- Fixed-seed schedule enumeration exhausts declared residues only for seed 0 and the three standard bands.
- The selected task-test aggregate is blocked by an inherited fixture portability defect even though the newly added tests pass independently.
## Current reviewer considerations

Source SHA-256: `1454bbd932334cd47503de4be8d3ff4b906db587b75416bca60d53475224efb6`.

# Decisions

## D1 — Preserve the canonical rule

The canonical Racket semantics were not changed. The selected rule hash remains `3d808db30609`. The authority repair was limited to making the executable `target_code` byte-for-byte canonical; archival `raw_code` was preserved as history. Changing the rule to resolve a generator defect was rejected because the existing rule correctly implements the ARC task and passes all canonical pairs.

## D2 — Use a narrow episode-level parameter only in a prototype

The proposed parameter is `four_region_color ∈ {4,7}`, chosen once per episode and held fixed across three demonstrations and one query. The canonical default `7` returns the exact canonical program. Setting `4` changes only the exceptional four-region mapping and leaves object selection, 4-connectivity, bounding boxes, and counts unchanged.

A connectivity parameter was rejected for the prototype because changing 4- to 8-connectivity alters the central reasoning operation and is already the principal shortcut the production curriculum must refute. The output-mapping parameter is smaller, preserves the original family structure, and can be identified from ordinary all-count examples.

## D3 — Alternate public and generalized scene classes

The default schedule declares period two: even indices use a varied official-family scene and odd indices use a generalized scene containing a 4-vs-8 connectivity witness. A lesson consists of three demonstrations followed by one query. This guarantees that every ordered four-pair window contains generalized support and that every query rotation still has a rival-refuting demonstration.

An unconstrained random scene mixture was rejected because it can generate an all-public lesson, and all canonical public pairs fit the 8-connectivity rival. A witness-only explicit override was also rejected because it would not protect the production sampler.

## D4 — Preserve exact profile controls

`scene_profile` remains the only advertised exact axis. Explicit overrides bypass the schedule and produce the requested profile. Public profiles now retain the canonical canvas dimensions in easy, medium, and hard; variation comes from legal object transformations and placement rather than growing the board outside canonical support.

## D5 — Declare the strongest plausible shortcut

The declared rival `eight_connected_zero_regions` uses 8-connectivity when counting zero regions inside each object's bounding box. It fits all four canonical pairs. The retained diagonal-contact witness produces color `2` under the intended rule and `1` under the rival. Generalized profiles are required to emit such a witness.

## D6 — Require strict scalar inputs

`seed` and `sample_index` now require literal non-boolean integers, and `sample_index` must be nonnegative. Silent coercion was rejected because it aliases distinct calls, weakens reproducibility, and caused the baseline defect-lint failure.

## D7 — Keep frozen-fixture failure honest

The inherited root fixture is explicitly frozen and uses a fixed `__file__.parents[...]` path that fails in the portable task-test runtime. It was not rewritten. New tests use `reviewer_support.find_root`, `load_selected_generator`, and canonical helpers and pass 26/26 independently. The overall completion state is therefore blocked only on maintainer migration of the inherited fixture, not reported as an aggregate pass.

## D8 — Evidence scope

The final production claim is limited to the selected generator hash `1454bbd932334cd47503de4be8d3ff4b906db587b75416bca60d53475224efb6`, the named rival contract, the three standard bands, and the retained seed ranges. The 300-lesson census and fixed-seed period enumeration are strong finite evidence, not proof against undeclared rivals or all possible seeds.
