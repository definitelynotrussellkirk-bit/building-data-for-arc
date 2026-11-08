# Working notes: 76e0bd03e098

## Current intended rule

For each nonzero color other than 8 that occurs exactly twice, process colors in
first-seen row-major order. Try the horizontal-then-vertical elbow against the
**original** input. If that path is clear, paint it; otherwise paint the
vertical-then-horizontal path without a second clearance requirement. Preserve
color-8 walls. Painting accumulates, so later colors overwrite earlier path
colors at intersections. Selected authority hash: `43d5e3caf0e0`.

## Current implementation

Version 2.0.0, SHA-256
`20d16fff8241c881bc0b27ae62c2813dd88b083d27745af7eebd5860896db93a`.
Every ordinary draw has three pairs and four/five walls and exposes all six
consequential distinctions: horizontal preference, vertical detour,
both-blocked vertical fallback, wall preservation, later-color overlap, and
row-major rather than numeric order. The two exact axes are `scene_profile` and
`n_walls`; unknown keys and invalid types fail loudly.

## Reversed decisions

v1.2.1 used broad rejection sampling, required a clear elbow for every pair,
advertised eight partly dead/aliased axes, and had only a permissive count-based
validator. Those choices were replaced because the baseline battery failed
`lint`, `defect_lint`, and `override`, and because the canonical blocked-fallback
example was unreachable. Evidence is in `checks/before/` and
`counterexamples/blocked_fallback/`.

## Evidence

- focused tests: 71/71 pass (`checks/task-tests/`);
- final battery: 12/12 stages green (`checks/final-battery/`);
- semantic census: 600/600 strict, 5/5 canonical, 6/6 witnesses/rivals;
- lesson census: 300/300 lessons, 1,500 rotations, zero declared-rival ambiguity;
- final visible-only solve: 4/4 demonstrations in revision 1, source-bound to the
  final generator hash.

The selected Racket authority was not changed. An independent reviewer oracle and
Racket parity helper live in `workspace/reference_probe.py`.

## Known limits and open findings

The construction is intentionally narrow: translation, horizontal reflection,
recoloring, shape padding, and one extra-wall choice yield six normalized
relative topologies in a 900-draw probe. This guarantees semantic teaching but
may permit geometry-template shortcuts. Future work should add independently
designed cores or constrained random synthesis while requiring the same six
witnesses and per-lesson rival kills. The current rotation evidence covers only
the six declared rivals; universal identifiability is not claimed.
## Current reviewer considerations

Source SHA-256: `20d16fff8241c881bc0b27ae62c2813dd88b083d27745af7eebd5860896db93a`.

# Decisions — 76e0bd03e098

## D1: Preserve the canonical authority

**Prior choice:** v1.2.1 described the task as "choose an elbow that does not
cross any wall" and required at least one clear elbow per pair.

**New choice:** pin `RULE_HASH = "43d5e3caf0e0"` and implement the actual
selected authority: H-first when clear in the original input, otherwise V even
when V is blocked; preserve 8-walls; paint in first-seen row-major color order;
later colors win overlaps.

**Reason/evidence:** all five canonical inputs and the explicit
`counterexamples/blocked_fallback/` witness require these semantics. Racket
parity is 120/120 in final rule smoke. Changing Racket would have hidden a
Python distribution error, so no authority source was edited.

**Reversal trigger:** only a new selected canonical authority or corrected
canonical labels, with a new rule hash and synchronized evidence.

## D2: Use branch-complete construction instead of broad rejection sampling

**Prior choice:** place random isolated pairs/walls and reject unless every pair
has at least one clear elbow. This excluded the authoritative fallback branch
and left other answer-bearing branches to chance.

**New choice:** start from one verified 8×10 teaching core containing three
roles—both-clear, H-blocked/V-clear, and both-blocked—then translate, horizontally
reflect, recolor, pad to one of five shapes, and choose four or five walls.
Every ordinary draw also contains selected-path overlap and nonnumeric processing
order.

**Reason/evidence:** the semantic gate measures every one of six witnesses on
600/600 final draws, and all six executable rivals are refuted. The alternative
of keeping random rejection plus post-hoc validation was rejected because rare
branches would remain difficult to guarantee in every lesson.

**Failure mode/limit:** topology can become a shortcut. The 900-draw normalized
self-review found six topologies (`checks/topology-self-review.json`). A future
broadening should add multiple independently designed cores or a constraint
solver, but must preserve per-lesson rival kills before replacing this version.

## D3: Make the advertised distribution contract exact and small

**Prior choice:** advertise eight axes (`grid_h`, `grid_w`, palette aliases,
size/count aliases, density, texture), several of which were dead, overlapping,
or incompatible with actual difficulty ranges. Unknown keys were silently
accepted.

**New choice:** expose only two pixel-recoverable axes:

- `scene_profile`: `8x10`, `8x11`, `8x12`, `9x10`, or `9x11`;
- `n_walls`: exactly 4 or 5.

Both have strict types, explicit unknown-key rejection, and an observer.

**Reason/evidence:** the final override matrix passes 1,620/1,620 draws with zero
findings. The baseline had 11,630 findings. Separate `grid_h`/`grid_w` axes were
rejected because the supported shape set is linked, not a Cartesian product.
Palette metadata was rejected because recoloring is latent randomness rather
than a promised semantic override.

**Reversal trigger:** add an axis only when its values are independently
constructible, observable from pixels, and covered by the override matrix.

## D4: Fix the role/order distribution deliberately

Three pair colors are sampled from ARC colors `{1,2,3,4,5,6,7,9}`; color 8 is
reserved for walls and 0 for background. Sorted selected colors are assigned to
roles as `max → fallback`, `min → preference`, `middle → detour`. Because the
fallback endpoint appears first in the core, first-seen order is max/min/middle
rather than numeric order. This makes the `numeric_order` rival visibly wrong
without assigning semantic meaning to any fixed color.

Three pairs are mandatory because the task needs simultaneous evidence for all
three route cases. Four walls are the minimum that preserve the selected scene's
blockers plus one harmless wall; the fifth adds controlled variation. Using
fewer pairs/walls or optional semantic roles was rejected because an individual
lesson could then omit a consequential branch.

## D5: Separate production code from the independent test oracle

`generator.py` contains a mirror and executable rivals because the shared
semantic gate needs callables. Tests additionally import
`workspace/reference_probe.py`, which independently derives color order,
endpoints, elbows, branch summaries, and optional real-Racket outputs. The
minimal blocked-fallback input/output pair is retained under `counterexamples/`.

This split catches accidental self-agreement between generator helpers and tests.
The focused suite first failed 57/71 cases against v1.2.1, then passed 71/71 after
the repair. A future agent should extend the independent probe rather than copy
new production helpers into tests.

## D6: Validate both grids and lessons

`self_check` rejects malformed/ragged/non-ARC inputs, wrong profiles, wrong pair
or wall counts, aligned endpoints, endpoint crossings, missing route cases, and
missing overlap. `strict_canonical_like` reuses this declared teaching manifold.
Six witnesses map one-to-one to six rivals: `vertical_first`, `horizontal_only`,
`clear_required`, `first_wins`, `numeric_order`, and `paints_over_walls`.

The generator deliberately does **not** claim universal `lesson_identifiable`.
The shared gate and the 300-lesson census establish no ambiguity only against
those declared rivals. Ordered production is the promised policy; query rotation
was tested diagnostically and happened to pass all 1,500 rotations.

## D7: Stop after a source-bound clean handoff

No changes were made to the generator after preparing the final solve episode.
The stopping criteria were: focused regressions green, 12/12 battery stages
green, the expanded lesson census clean, both audits documented, and a fresh
patch-apply copy reproducing the source hash and focused tests. Remaining work is
geometry broadening rather than a correctness blocker.
