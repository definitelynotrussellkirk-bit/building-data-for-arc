# Working notes: 58cc346198c0

## 2026-09-28 review repair

The strongest missed rival was **per-color bounding boxes**: merge every cell of a color, even when that color occurs in disconnected components, and draw one global set of four corners. All four canonical demonstrations and every v2.0.0 generated scene used a unique color per object, so this wrong rule was observationally equivalent to the intended per-component rule.

Version 2.2.0 adds an exact observable `palette_pattern` axis with `distinct` and `repeat_pair` values. The four-position schedule alternates them so every two-example lesson contains a repeated-color counterexample while the one-in-four canonical-profile anchor remains distinct. `per_color_bbox` is now a declared canonical shortcut/lesson competitor, and `separated_same_color_objects` is its task-linked witness.

The previous `irregular` family was only two base shapes under D4 transforms (12 normalized variants, sizes 5 or 6). It is now produced by bounded deterministic connected growth, with rejection for line-like, full-box, L-template, or zigzag-template cases and a fixed-template fallback only if growth cannot realize a legal shape. A focused 80-draw test requires at least one size-8-or-larger object and at least 24 normalized irregular shapes.

The canonical Racket authority was not changed. Independent Racket application agrees with the Python test mirror on the explicit same-color counterexample in `QUESTION_ANSWER.md`, and authority synchronization remains green.

## Residual limitations

- The curriculum still uses rectangular slots separated by a blank row or column. This is intentional isolation for the component rule, but it leaves coarse quadrant placement somewhat predictable.
- L and zigzag branches remain finite transformed template banks. The irregular branch is now broad enough to prevent the whole task from collapsing to those templates, but future loss probes may justify procedural L/zigzag variants too.
- `strict_canonical_like` deliberately excludes repeated-color scenes because the four canonical inputs use distinct object colors. The after census still clears the declared 20% strict-profile floor at 145/600 (24.2%).
## Current reviewer considerations

Source SHA-256: `9a65814c78a31ad337fa17f63c6237ebf64cea312f4c92c7f40a919d2e0c6f8e`.

# Design decisions: 58cc346198c0

## Intended unit of transformation

**Choice:** treat each 4-connected same-color component as an object, even when two components share a color.

**Original rationale:** the canonical Racket authority calls `objects` and transforms each object independently. The v2.0.0 generator’s stronger invariant—one unique color per object—appears to have been a construction convenience rather than a requirement of the task; no retained note justified making color identity equivalent to object identity.

**Alternatives considered:**

- Keep unique colors and merely document connectivity. Rejected because it leaves connectivity observationally irrelevant.
- Use diagonal same-color separation only. Rejected because it would entangle the witness with uncertainty over 4- versus 8-connectivity.
- Add arbitrary repeated palettes. Rejected because multiple repeated groups make the axis harder to observe and can introduce accidental overlaps.

**Probe:** an exact two-object same-color grid was run through the Python mirror and an independently opened canonical Racket oracle. Both produced two separate four-corner outputs; the global per-color rival produced one four-corner output.

## Palette axis

**Choice:** add `palette_pattern` with exact values `distinct` and `repeat_pair`.

`distinct` preserves the canonical palette pattern. `repeat_pair` duplicates exactly one selected nonzero color and shuffles its component assignments using a keyed RNG. For four objects its component-color multiplicities are exactly `[1, 1, 2]`; for two objects both components share the one color.

**Failure modes guarded:**

- same-colored components accidentally touching and merging: prevented structurally by blank slot separators and checked through object count;
- two repeated color pairs or a color used three times: rejected by `self_check`;
- hidden override semantics: `observe_overrides` reconstructs the exact palette pattern, and the full override matrix passed.

## Lesson schedule

**Choice:** alternate distinct and repeat-pair scenes while alternating mixed and single shape families:

1. `mixed_l_zigzag_distinct`
2. `l_shape_repeat_pair`
3. `mixed_zigzag_irregular_distinct`
4. `irregular_repeat_pair`

**Rationale:** `EXAMPLES_NEEDED` is two. Every circular two-position window therefore contains at least one repeat-pair counterexample and at least one mixed-family scene. Positions 0 modulo 4 remain distinct, preserving the existing canonical dimension anchors and enough strict-profile mass.

**Alternative considered:** make every scene repeat a color. Rejected because the canonical demonstrations have distinct colors and the strict canonical-profile census should retain meaningful support.

**Probe:** all four two-example schedule windows pass `lesson_identifiable`, and the semantic gate materialized 12/12 identifiable lessons across easy, medium, and hard.

## Rival and witness declarations

**Choice:** register `per_color_bbox` as a semantic rival, lesson competitor, and canonical shortcut; register `separated_same_color_objects` as its witness.

**Rationale:** this turns the review conclusion into an executable contract rather than prose. The gate must establish all three facts: the rival fits the canonical examples, the witness fires in generated data, and the rival disagrees with the authoritative Racket output on witness cases.

**Probe:** after-gate result: canonical ambiguous shortcut `per_color_bbox`; witness satisfaction `separated_same_color_objects`; 60/60 authoritative rival checks held; witness fired 314/600 draws.

## Irregular shape distribution

**Choice:** replace random selection from 12 fixed irregular variants with bounded procedural connected growth.

The growth process chooses a local bounding region, grows from a seed through orthogonal frontier cells, normalizes the result, and accepts only connected shapes spanning both axes with at least one non-corner cell and at least one absent bounding-box corner. Known L and zigzag templates are rejected from this branch. The old irregular bank is retained only as a guaranteed fallback.

**Original rationale:** prior retained evidence already identified the finite template family as a limitation and recommended procedurally grown polyominoes.

**Alternatives considered:**

- Enumerate a larger static bank. Rejected because it postpones rather than removes template memorization.
- Generate all polyominoes exhaustively. Rejected as unnecessary and more complex for small slots.
- Remove named shape families entirely. Rejected because mixed/single-family lessons are useful explicit controls for the existing L-only rival.

**Probes:** focused 80-scene census requires 24 or more normalized irregular shapes and a maximum size of at least 8; the full diversity gate reported 100% unique inputs and outputs.

## Dimensions, object count, and placement

**Choice:** retain the 7–14 by 9–15 grid ranges, 2–4 object range, canonical profile anchors, and blank-separated slots.

**Rationale:** these axes already passed morphology, canonical-profile, override, and diversity gates. Changing them was not necessary to repair the identified semantic defect. Blank separators also guarantee that reused colors remain separate 4-connected components.

**Known limitation:** slots create regular coarse positions. A future revision should change this only with a packing test that preserves guaranteed component separation and exact override realizability.

## Canonical-profile predicate

**Choice:** require a distinct palette in `strict_canonical_like` while allowing repeat pairs in the broader teaching grammar.

**Rationale:** all four canonical inputs use a distinct color per object. Labeling a repeat-pair scene “strict canonical-like” would inflate the profile measurement. The after strict rate remains 24.2%, above the declared 20% floor.

## Racket authority

**Choice:** no Racket change.

**Rationale:** the canonical rule already handles disconnected same-color objects correctly. Independent application to the exact counterexample matched the Python mirror, rule smoke passed, and authority synchronization/execution parity remained green. The defect was wholly in the generated input distribution and declared semantic competitors.
