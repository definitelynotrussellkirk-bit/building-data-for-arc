# Current design — 6737eb62cf42

## Intended rule and authority

Crop the input to the smallest axis-aligned rectangle containing **every nonzero cell**, preserving colors and all zeros inside that rectangle. The canonical Racket program is unchanged and pinned by `RULE_HASH = "debb1a8a129a"`; Python helpers are checks, not label authority.

## Version 3.0.0 distribution

The previous broad API contained dead, overlapping, and band-clamped controls. Version 3 exposes four exact pixel-observable axes:

- `scene_profile`: five canonical input/crop shape pairs;
- `placement`: upper/lower × left/right, with one-cell exterior padding;
- `palette_size`: 2–4 nonzero colors;
- `texture`: `paired_objects` or `singleton_extreme`.

The 20-slot default schedule cycles every profile and placement, alternates textures, and uses three demonstrations plus one query. `paired_objects` gives all colors repeated. `singleton_extreme` puts a singleton color at the lower-right crop boundary, so cropping only repeated colors or only the two most frequent colors fails. Difficulty keeps the same public axes but deterministically rotates the primary motif; easy/medium/hard are therefore not byte-identical.

## Semantic contract

Declared rivals are `repeated_colors_only`, `two_most_frequent_colors`, and `largest_monochrome_component`. Declared witnesses cover all objects defining the crop, a singleton color defining a boundary, and a third color defining a boundary. `schedule_profile`, `lesson_identifiable`, the independent task-local probe, and the retained Racket-labelled counterexample make those claims executable.

## Measured final state

Generator SHA-256: `750b889656a349294e797f568e578ef3b6da9a191c32f24048bbc794b2cf7647`.

- 12/12 required battery stages green with query rotations required.
- 650/650 focused tests green.
- 300 lessons, 1,200 pairs, and 1,200 query rotations: zero declared-rival ambiguities; 1,139 unique inputs.
- Complete 480-case public override product: zero errors.
- All 80 schedule windows and 320 rotations across four difficulty settings: zero ambiguities.
- Canonical-profile floor: 26/60 exact hits, with support in every band.

## Known limits

The finite rivals do not prove universal identifiability against every program. Shapes are intentionally limited to the five canonical-scale profiles and a fixed zero background; this is a curriculum choice, not the full mathematical domain of the crop rule. Catalog approval/train safety remains outside this review.
## Current reviewer considerations

Source SHA-256: `750b889656a349294e797f568e578ef3b6da9a191c32f24048bbc794b2cf7647`.

# Design decisions — 6737eb62cf42

## D1 — Keep the canonical Racket authority unchanged

The executable rule already matches all five canonical labels: crop to the tight bounding box of every nonzero cell. The failures were generator/contract failures, so changing the rule would create needless authority drift. `RULE_HASH = debb1a8a129a` is pinned and the authority-sync stage is green.

## D2 — Replace the nine-axis legacy surface with four exact axes

The old version advertised controls that were dead, aliases, clamped by difficulty bands, or only meaningful in degenerate branches. I retained only `scene_profile`, `placement`, `palette_size`, and `texture`, each recoverable from returned pixels. Unknown keys and invalid types/enums are rejected. The complete 480-member cross product passes exact round-trip validation.

Rejected alternative: patch each legacy axis individually. That would preserve overlapping meanings and make exact observation fragile without adding useful task diversity.

## D3 — Use five canonical-scale shape profiles

The public profiles are the five observed input/crop shape pairs, not exact canonical placements. This guarantees profile-floor support while still varying colors, motif, placement, and texture. It intentionally does not claim the full unbounded crop-rule domain.

Rejected alternative: arbitrary grid/crop dimensions. It adds breadth but weakens canonical support and makes curriculum qualification larger without addressing the actual shortcut.

## D4 — Alternate paired and singleton-extreme textures

Paired cases resemble all canonical examples. Singleton-extreme cases put a once-occurring color at the lower-right crop boundary. They directly refute `repeated_colors_only` and `two_most_frequent_colors`; every case refutes `largest_monochrome_component`.

Rejected alternatives: interior singleton cells, which do not change crop boundaries; and random singleton frequency, which can create witness-free lessons.

## D5 — Deterministic 20-slot curriculum, three demonstrations plus one query

Five profiles × four placements form a 20-slot period. Alternating texture gives every four-pair lesson both ordinary and counterexample structure. All 80 cyclic windows and 320 rotations across `None/easy/medium/hard` pass the declared-rival hook; the production census independently checks 300 sampled lessons and 1,200 rotations.

## D6 — Make difficulty observable without changing the public semantic axes

The defect linter found easy/medium/hard byte-identical. A band-specific offset now rotates among four primary motifs while preserving requested profile, placement, palette size, and texture. This avoids inventing a misleading “difficulty” semantic rule.

## D7 — Retain failures and portable probes

Red tests preserve the missing-difficulty, missing-`schedule_profile`, and missing-counterexample failures. `workspace/reference_probe.py` imports the actual rival declarations, exhausts the public override product, checks cyclic schedule/query rotations, and emits the exact witness input. The retained counterexample is Racket-labelled and portable.

## Limits

Finite rivals are not a proof of unique induction. The background remains fixed at zero; color-role permutations and arbitrary dimensions were not claimed. Catalog approval and training admission were not changed.
