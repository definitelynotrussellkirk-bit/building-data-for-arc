# Working notes: 629901f9cf30

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 review repair

### D1. Rule confirmation

The preserved authority performs a Manhattan Voronoi fill from every nonzero cell. A cell receives a color only when its nearest seed color is unique; equal-distance nearest colors leave 0. The independent oracle in `workspace/reference_probe.py` matches all three labeled canonical pairs, whose tie-cell counts are 6, 3, and 6. No Racket edit was needed.

### D2. Honest exact axes

The prior metadata mixed three meaningful controls with palette aliases, constants, density aliases, and degenerate texture modes. The reviewed API exposes only `grid_h`, `grid_w`, and `n_seeds`. Dimensions accept the full 4–18 range and seed count accepts 2–6 in every difficulty band.

Unknown axes, bools, strings, floats, invalid difficulty values, and out-of-domain integers are rejected before sampling. Difficulty changes dimension weighting only and never narrows an exact override domain.

### D3. Constructive tie witness

Random sparse seeds did not guarantee the rule's defining tie branch. The repaired sampler first chooses a horizontal or vertical length-three template, places two differently colored seeds at its endpoints, and reserves the midpoint. Every additional seed is placed outside that midpoint. The midpoint therefore remains tied at distance one (possibly among more than two colors) and the correct output remains 0 there.

This is constructive rather than rejection-based and works for every legal 4×4 through 18×18 geometry and every legal seed count.

### D4. Period-three seed-count curriculum

`SCHEDULE_PROFILES = (three_seeds, four_seeds, six_seeds)` with `EXAMPLES_NEEDED = 3`. Every consecutive three-demo window contains two scenes with more than three seeds. The rival `first_three_seeds_only` fits all three canonical pairs because each canonical input contains exactly three seeds, but it is refuted by every scheduled four- or six-seed scene.

The tie-policy rival `lowest_color_on_ties` is refuted by every generated grid. Declarations are aligned across `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.

### D5. Pixel-derived validator and oracle mirror

`self_check` and `strict_canonical_like` require rectangular literal ARC grids, dimensions 4–18, 2–6 nonzero cells, distinct seed colors, and at least one actual nearest-color tie. `observe_overrides` recovers all exact axes from returned pixels. `rule_mirror` computes Manhattan distances directly and preserves tie-zero semantics.

A two-adjacent-seed scene, which has no integer tie locus, is rejected. Duplicate seed colors and malformed grids are diagnostic rather than exceptional.

### D6. Independent reusable probe

`workspace/reference_probe.py` does not import generator parsing or Voronoi helpers. It independently loads canonical pairs, parses seeds, computes Manhattan labels, detects ties by comparison to a lowest-color tie policy, implements the first-three rival, and audits determinism, diversity, branches, and canonical fit.

Evidence retained under `WORK/checks/629901f9cf30-*`:

- RED: 24 failed / 17 passed, including branch-limited endpoints, ignored controls, missing tie guarantees, and absent semantic contracts.
- GREEN: 41/41 focused tests passed.
- Independent audit: 180 samples per band (720 total), zero validation errors, zero nondeterminism, 720 distinct inputs, 720 tie witnesses and tie-policy refutations, and 480 first-three-seed refutations. All three canonical pairs matched the oracle and the canonical shortcut.

### Known limits

Seed colors are unique within a scene because same-color nearest ties are not visually distinguishable from a unique nearest color. The reviewed training grammar does not include zero-seed, one-seed, or repeated-color degenerates. Those remain executable rule inputs but are intentionally outside this lesson generator.


### D7. Source-bound rotation verification

The repaired period was enumerated through the production sampler with every labelled pair held out once in easy, medium, and hard bands. The blocking schedule receipt passed: each rotation retained a tie-policy witness and at least one four- or six-seed demonstration that refuted `first_three_seeds_only`. The independent probe now repeats the same finite check without the shared census machinery and reports 48/48 clean rotations across the four local bands. This is fixed-seed finite evidence, not a proof over every seed.
