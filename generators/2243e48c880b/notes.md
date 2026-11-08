# Working notes: 2243e48c880b

## Intended rule and domain

Find exactly three nonzero monochromatic 4-connected components in row-major
discovery order. Stably sort them by cell count and paint the ranked components
2, 4, and 8 on a blank grid. Equal sizes are lawful; stable sort means their
row-major discovery order breaks the tie. Disconnected components may share an
input color because input color is not a semantic object identity.

The selected sampler emits 8–12 by 9–14 grids, three components of size 2–6,
four size relations (`distinct`, `smallest_tie`, `largest_tie`, `all_tied`),
and one to three nonzero input colors. `self_check` deliberately accepts all
four canonical inputs, including canonical sizes `[4, 5, 5]`.

## Reversed prior decisions

The imported v2.0.1 generator required three distinct sizes and three distinct
colors. That restriction contradicted the canonical tie and made every public
demonstration compatible with the shortcut “rank objects by total frequency of
their input color.” Version 3.1.0 removes both restrictions. Two-color examples
repeat one color on the smallest and largest rank, so total-color frequency
orders the unique middle color first and is observably wrong. The retained
Racket-backed witness is `counterexamples/color_total_frequency.json`.

The first v3 draft sampled every axis independently. Although individual
witnesses were common, the public semantic gate found 4/12 unidentifiable
three-demo lessons and the canonical-profile envelope was only 12/60. The final
default uses a three-slot schedule: smallest-tie/two-color, largest-tie/two-color,
then distinct/three-color canonical-profile anchor. Every consecutive four-pair
window remains identifiable under all four query rotations against the declared
rivals, while exact overrides retain the full lawful joint axis domain.

## Executable contracts

`CANONICAL_SHORTCUTS` declares the strongest public-fitting rival,
`color_total_frequency`. `LESSON_COMPETITORS` additionally checks row-major-only,
reverse-equal-tie, numeric-input-color, and descending-size rules. Matching
semantic witnesses and `lesson_identifiable` are executable. The source-bound
`workspace/lesson_probe.py` imports those declarations rather than copying a
rival list and exhaustively rotates consecutive lesson windows.

## Known limits

The finite rival set is not a proof of unique induction against every possible
program. The Python `rule_mirror` is an authoring oracle; final acceptance also
uses the selected Racket authority. Shape growth is stochastic but deterministic
for `(seed, sample_index, version, difficulty)` and may not cover every free
polyomino. Output colors 2/4/8 and exactly three components are fixed by the
selected rule; this generator intentionally does not extrapolate beyond that
domain.
## Current reviewer considerations

Source SHA-256: `5c0a262fd374920711ded2efde6584b8dff56bc4775a96628546cfd5bba1558f`.

# Decisions

## D1 — Preserve the selected authority

The Racket rule and canonical ledger were not changed. `RULE_HASH` is pinned to
`d78310e1c969`; the final rule-smoke and authority-sync stages pass. The repair is
strictly an input-distribution and executable-contract change.

## D2 — Model monochromatic connected components, including stable ties

The old sampler required three distinct sizes even though canonical pair 2 has
sizes `[4,5,5]`. The repair accepts four size relations: distinct, smallest tie,
largest tie, and all tied. Components are discovered row-major and Python's
stable size sort mirrors the authority's equal-size tie behavior. Rejecting ties
was discarded because it excluded a canonical semantic distinction.

## D3 — Allow repeated input colors

The old distinct-color restriction made “component size” indistinguishable from
“total frequency of the object's color” on every example. One- to three-color
inputs are now lawful. In two-color cases, the smallest and largest ranked
components share a color, giving a direct counterexample to the strongest
canonical-fitting shortcut. Keeping colors distinct was rejected because it
preserved that shortcut.

## D4 — Expose only four exact observable controls

The selected axes are `grid_h` (8..12), `grid_w` (9..14), `size_pattern`, and
`palette_size` (1..3). Unknown and invalid values fail before construction, and
`observe_overrides` recovers the realized values. The final override gate accepts
**12,600/12,600 draws across 140 cases and three bands** with zero findings.
Decorative or non-observable controls were not added.

## D5 — Use a three-slot lesson schedule

The first repair sampled every control independently. Its intermediate battery
had 10 green stages but failed profile floor (12/60 envelope hits) and semantic
gate (4/12 lessons unidentifiable). The final defaults cycle:

1. smallest-size tie, two colors;
2. largest-size tie, two colors;
3. distinct sizes, three colors, one of four canonical-profile dimensions.

The first two slots directly refute all declared rivals; the third maintains
canonical profile support. This gives every consecutive four-pair window at
least one counterexample after any query rotation. Pure independent sampling was
rejected because aggregate witness frequency did not guarantee teachable
three-demo lessons.

## D6 — Declare executable rivals and witnesses

`CANONICAL_SHORTCUTS` contains `color_total_frequency` because it fits all four
canonical pairs. `LESSON_COMPETITORS` additionally covers row-major-only,
reverse-equal-tie, numeric-input-color, and descending-size rules. Each has an
executable witness, and `lesson_identifiable` requires every competitor to fail
on at least one demonstration. These checks establish finite declared-rival
coverage, not universal uniqueness.

## D7 — Add focused tests and a reusable source-bound probe

The task-local suite covers all canonical pairs, all 36 exact pattern/palette/
difficulty combinations, malformed overrides, deterministic generation, the
retained Racket counterexample, the default schedule, every cyclic lesson start,
and the workspace probe itself. Final count: **55/55**. The reusable
`workspace/lesson_probe.py` imports the generator's actual rival declarations;
it checked **108 consecutive lessons and 432 rotations** with no failures.
Copying rival names into a second hardcoded list was rejected because it could
drift from production declarations.

## D8 — Retain failures and state the limits

The complete baseline battery (5 failed stages), the intermediate after battery
(2 failed stages), final evidence, and exact counterexamples are retained. The
Racket-backed final census covers 300 lessons, 1,200 unique pairs, and 1,200
rotations with no declared-rival ambiguity. This is finite evidence only. The
default schedule correlates palette size with tie profile; exact overrides and
tests cover the full lawful control domain, but arbitrary undeclared piecewise
rivals remain outside the claim.

## D9 — Keep audit work source-bound and non-invasive

The two assigned audit targets were not edited. `19496da22435` has a reproduced
override-contract defect. `77871cecd343` retains a second-order default-schedule
shortcut reproduced against the assigned hash and selected Racket authority.
