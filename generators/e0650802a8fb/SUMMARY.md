# e0650802a8fb — fill diagonal spans between matching endpoints

Selected implementation: `generator.py` version `3.0.0`.
Canonical authority is unchanged and pinned by `RULE_HASH = "040cfb38300e"`.

## Input curriculum

Each ordinary input has a zero background and 2–4 colors that each occur exactly
twice on a non-trivial 45-degree diagonal. The rule scans nonzero colors in
row-major first-appearance order and paints each inclusive diagonal span. Later
colors overwrite earlier colors at crossings, including at an earlier color's
original endpoint.

A deterministic five-profile schedule covers:

1. disjoint diagonal spans;
2. an interior crossing whose owner disproves numeric color priority;
3. an endpoint crossing where the original endpoint is overwritten;
4. the complementary endpoint-order case where that endpoint survives; and
5. a controls scene with one inert axis pair, singleton, and triple.

Every five consecutive sample indexes contain all five profiles. The exact
advertised axes are `grid_h` (8–14), `grid_w` (8–14), `pair_count` (2–4), and
`scene_profile`; unknown or invalid overrides are rejected.

## Semantic contract

`LESSON_COMPETITORS` names seven executable rivals covering numeric ordering,
endpoint preservation, midpoint-only fill, one-slope-only fill, axis filling,
and ignoring the exactly-two guard. The controls profile specifically separates
the two shortcuts that fit all five canonical pairs: `fill_axis_pairs_too` and
`outermost_cells_even_when_repeated`.

`workspace/lesson_probe.py` checks canonical parity, exact axes, every cyclic
start of the five-profile schedule, and refutation of the generator's declared
rivals. It reads rival declarations from the selected source rather than keeping
a second hard-coded list.

## Final verification

Generator SHA-256:
`9edaeb09de4a1961f9556220121fc4ee8ab4d09a3ca626c568ba7f03da5e6abc`.

The completed after battery passed all 12 required stages. The focused task test
suite has 12 tests. A 300-lesson production census (100 per band) reported zero
ambiguous lessons, hook warnings, or scoring errors; every declared rival was
refuted in every lesson. The cyclic probe passed 300 overlapping windows and all
five exact-axis cases. Full evidence is retained under the packet's `checks/`.

Approval and training admission remain catalog-derived; this repair does not
change them.
