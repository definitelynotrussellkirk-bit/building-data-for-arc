# Working notes: 8dac9e436a4c

## 2026-10-07 review-95c2d465e72fe468

### Root causes

The imported v2.0.1 sampler advertised nine axes but generated from its own RNG ranges, so exact size/count/texture requests were absent or misleading. `self_check` only required a color-6 cell and trusted `meta.texture == "no_frame"` to waive validation. The generator had no `RULE_HASH`, no semantic witnesses/rivals, sparse exact canonical-profile support, and selected-authority text differed from canonical/archival text. An early repair draft also used an exponential exhaustive placement search.

### Repair

- Pinned `RULE_HASH = 1ee9a2a0fa3f`; canonical Racket semantics are unchanged.
- Reduced the override contract to four exact numeric axes and made the complete Cartesian domain constructive.
- Added pixel-derived frame/solid/decoration validation, explicit negative mutations, and lawful edge cases.
- Added canonical-dense dimensions, active difficulty, square/wide/tall frames, and bounded nine-anchor placement.
- Added an alternating two-profile lesson schedule, executable witnesses/rivals, and rotation-aware lesson identification.
- Added 59 portable task tests and independent `workspace/reference_probe.py` tooling.
- Synchronized selected base `target_code` with already-authoritative canonical/archival text.

### Final evidence

- Before battery: 6 green, 2 advisory, 4 failed.
- After battery: 12/12 green.
- Task tests: 59/59 passed.
- Stress: 2,096 draws, zero errors; 753 unique ordinary inputs.
- Semantic rotation gate: 48/48 identifiable.
- Lesson census: 300 lessons, 1,200 unique pairs/rotations, zero declared-rival ambiguity.

### Known limits

Ordinary generation caps frames and solids at two, placement uses a finite anchor family, and identifiability is established only against the declared rivals. Independent maintainer replay is still required before approval.
## Current reviewer considerations

Source SHA-256: `9498e7a7b0517f4d7a440ea744d75300b260c0f2655e0be8ba1e168a7a984969`.

# Decisions for 8dac9e436a4c

## Evidence baseline and prior leads

The packet's selected baseline, not any historical claim, was treated as source of truth. `evidence/associated_notes.jsonl` was empty, so no prior return was used as a repair lead. The immutable baseline battery measured 6 green stages, 2 advisories, and 4 failures. The original rationale for many v2.0.1 declarations is unknown; descriptions below distinguish what the old code did from what its author may have intended.

## Preserve the rule; synchronize only selected authority text

Canonical examples and the executable Racket rule agreed on a simple component rule, and rule smoke passed before repair. There was no semantic justification for rewriting it. The only authority edit copies the canonical program text into the task's selected `target_code`, making canonical, selected, and archival text byte-identical while keeping `RULE_HASH = 1ee9a2a0fa3f` and behavior unchanged.

Alternative rejected: changing the Racket code merely to make text synchronization easier. That would add semantic risk to a generator-distribution repair.

## Public controls: four exact numeric axes

The retained axes are:

- `grid_h`: integer 8–16;
- `grid_w`: integer 8–16;
- `n_frames`: integer 1–2;
- `n_solids`: integer 1–2.

Each is independently observable from pixels and constructively honored throughout the complete declared Cartesian domain, including 8×8 with two frames and two solids. Unknown keys, booleans, non-integers, and values outside the declared ranges are rejected.

The old `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, and `texture` declarations were removed because they were aliases, singletons, unobserved, or bypassed ordinary validation. Difficulty remains a supported sampler argument, not an advertised exact override: it changes frame scale and decoration length but does not promise one exact pixel statistic.

Alternative rejected: retaining decorative axes for apparent richness. An honest smaller contract is more useful than an unfalsifiable large one.

## Counts and lawful edge cases

Ordinary samples always contain one or two hollow frames and one or two solid distractors. Requiring a solid in ordinary lessons continuously teaches the distinction between a border and a filled rectangle. Two explicit lawful edge fixtures (`no_solid`, `both_hollow`) test rule generality outside the ordinary distribution; `no_hollow_frame` is an explicit negative mutation that `self_check` must reject.

The baseline advertised up to three frames and zero solids, but did not honor these counts exactly. I chose 1–2 for both ordinary exact axes because this complete domain is constructively packable at the smallest public grid and covers the two strongest teaching contrasts. The Racket rule itself remains valid beyond this generator grammar.

Alternative rejected: exposing 1–3 frames and 0–2 solids before proving every joint combination packable and pedagogically useful.

## Canonical-dense dimensions with broad support

When neither dimension is overridden, four of every five sample indices draw one exact canonical `(height, width)` pair from `(8,12)`, `(9,10)`, `(9,13)`, `(10,11)`, and `(11,11)`. The fifth explores the full 8–16 range. This makes the 20-draw profile floor robust while retaining broad shape support. An explicit height or width request remains exact and independent.

Alternative rejected: canonical dimensions only. That would pass the floor but unnecessarily narrow robustness. Uniform 8–16 only was also rejected because exact canonical joint profiles became too sparse in small gates.

## Constructive object layout

Every rectangle is placed from at most nine anchors: corners, edge midpoints, and center. A bounded backtracking search enforces at least one blank row or column between every color-6 bounding box. Shape candidates fall back deterministically from difficulty/family-preferred dimensions to 3×3.

An earlier repair draft enumerated every top-left coordinate. Failed large-shape probes could then explore up to roughly `196^4` tuples before fallback, causing multi-minute checks. The bounded anchor set reduces this to at most `9^4` tuples while retaining all corner packings needed by the declared domain.

Alternative rejected: randomized retry loops. They make exact overrides probabilistic and can hide rare impossible combinations.

## Difficulty and visual variation

Frame families are square, wide, and tall. Easy prefers small candidates and a one-cell decoration; medium prefers middle scale and a two-cell decoration; hard prefers large candidates and a three-cell decoration. Color, orientation of the decoration, positions, canonical/broad dimensions, and count profile continue to vary deterministically from the generation context.

Alternative rejected: pixel-identical difficulty aliases. Independent battery evidence explicitly flagged dead bands in an earlier draft.

## Lesson assembly and shortcut control

`EXAMPLES_NEEDED = 3`. Pair profiles alternate by sample index:

1. `multiple_frames`: two frames, one solid;
2. `extra_solids`: one frame, two solids.

A production lesson has three demonstrations and one query. In every four consecutive pairs, any held-out query leaves at least one two-frame demonstration. That refutes `first_frame_only`; the ever-present solid distractor refutes `fill_all_rectangles`. `lesson_identifiable` scores both executable rivals against demonstrations and query.

The strict semantic gate checked 48 rotations; the larger census checked 1,200. Both reported zero ambiguity. This supports the actual four-pair rotating-query policy, not arbitrary lesson lengths or every conceivable rival.

Alternatives rejected:

- a three-slot schedule with only one multi-frame pair, because holding that pair out made the shortcut survive;
- relying on witness frequency alone, because frequency does not guarantee every complete lesson identifies the rule;
- claiming universal identifiability from a finite rival set.

## Validation and independent tooling

`self_check` derives all claims from pixels. It checks rectangularity, integer colors, dimensions, absence of input color 8, exact frame/solid component structure, at least one hollow frame, count ceilings, empty frame interiors, and one straight external decoration. Metadata cannot waive these checks.

`workspace/reference_probe.py` independently reimplements component analysis, intended output, canonical profile extraction, and both rivals without importing production helpers. It is used by portable task tests and is retained for future reviews. `checks/stress_probe.py` demonstrates how to exhaust the joint public-axis domain and sample ordinary coverage.

## Limitations

- The generator grammar intentionally caps ordinary frames and solids at two each even though the rule is more general.
- Placement uses a finite anchor family; it is broad enough for the declared grammar but not a uniform sampler over all legal layouts.
- Semantic evidence rules out the declared `first_frame_only` and `fill_all_rectangles` rivals only. Unique induction against all possible hypotheses is unknown.
- Local checks do not grant catalog approval or training safety; independent maintainer replay remains required.

## Current native parametric candidate

The approved production source and exact canonical program are unchanged.
`workspace/parametric/` adds `match_policy=fill_only|area_match`: complete every
hollow frame, measure the unique largest newly filled color-8 component, then
recolor the separate solid color-6 rectangle with equal occupied area to 3.
The payload's different aspect ratio defeats simple shape/dimension matching.
A smaller filled region and its own matching solid support a causal ablation.

Independent 2–6 demos and 1–4 query prefixes share the same setting-neutral
inputs. Four queries include substantive 30x30 content (five frames, seven
solids) in a seed-shuffled position, not a fixed final-query position. Masking
exposes just one query to the existing controller.

Self-review found a real ordinal-area shortcut: with only three solids, the
median/second-smallest/second-largest rule fit every demo yet failed the large
query. Strengthening the second demo with additional solid distractors fixes
all three without increasing the two-demo minimum. The failing regression and
20 protected-Racket before/after evaluations are retained in the return checks.
The current task-local audit reports 800 count/setting requests over 20 seeds,
5,200 pair checks, 400 matched-input comparisons, 2,000 public-turn projections
and 104 protected-Racket evaluations. All 83 changed-target tests passed (59
existing and 24 parametric). These counts do not imply independent samples or
universal uniqueness. See the workspace README for exact reproduction/limits.

Separate native qualification and source-bound wrong-intermediate evidence
support owner acceptance; they do not confer it or admit training data.
