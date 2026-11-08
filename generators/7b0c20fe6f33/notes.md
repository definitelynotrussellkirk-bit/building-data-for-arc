# Working notes: 7b0c20fe6f33

## Intended rule

The unique blue marker (1) and red marker (2) define `(dr, dc)`. Preserve the
input, and paint color 8 at every in-bounds position obtained by translating a
green (3) source cell by that vector. The executable authority remains pinned to
rule hash `6f9c816ac7aa`.

## 2026-10-07 repair decision

The imported version `2.1.0` advertised nine axes but naturally emitted exactly
four scattered green cells, selected only four short knight-like vectors, did
not consume `vector_choice`, accepted unknown overrides, and treated invalid
negative fixtures as valid texture values. It also lacked `RULE_HASH`, and the
selected duplicate Racket text differed from canonical raw source by comments.
Baseline evidence is retained under `checks/before/`; four of twelve blocking
stages failed.

Version `3.0.0` replaces that sampler with a constructive, observable domain:

- dimensions independently span 9–16;
- 16 vectors include all three canonical long vectors, the legacy short vectors,
  sign variations, and four cardinal vectors;
- 11 connected motifs cover 3, 4, and 5 cells, including the canonical L,
  nonrectangular larger objects, and rectangular controls;
- every advertised axis combination is constructive on every difficulty band;
- unknown, mistyped, and out-of-range controls fail loudly;
- invalid degenerate textures are no longer part of the valid input grammar.

A deterministic four-position curriculum is
`canonical → extended → legacy_bridge → cardinal`. Any three positions contain
at least one nonlegacy vector, one object larger than three cells, and one
nonrectangular object. Declared rivals test the old small-vector restriction,
copying only the first three cells, and copying the filled bounding box.
`lesson_identifiable` checks every query rotation against those rivals.

## Evidence and limits

`generators/7b0c20fe6f33/tests/test_generator_7b0c20fe6f33.py` contains 2,140
portable tests, including all 2,112 exact combinations of 4 difficulty settings,
3 representative dimensions, 16 vectors, and 11 motifs. The final battery is
12/12 green; its override stage accepted 64,620/64,620 draws with zero findings.
The larger census materialized 300 four-pair lessons and checked 1,200 query
rotations with zero ambiguity.

The authority JSON was synchronized by making `target_code` byte-identical to
its existing `raw_code`; this removed two comments only. The executable rule,
rule hash, and behavior did not change.

The domain is intentionally finite: it does not claim all possible vectors or
all connected polyominoes, and the rival census is not a proof against every
conceivable shortcut. Source/translated-object and marker collisions are
excluded so labels remain visually unambiguous.
## Current reviewer considerations

Source SHA-256: `51e586a6770ba1f62a4b6d7e7c4c0b278de3358a7ddc6a4997b9f001493852ee`.

# Decisions — 7b0c20fe6f33

## D1. Replace decorative axes with four exact, observable axes

**Prior choice:** nine advertised axes, including singleton palette/density
fields and a texture axis containing invalid fixtures. Several were never read.

**New choice:** expose only `grid_h`, `grid_w`, `vector_choice`, and
`motif_choice`. Every value is consumed through `GenCtx`, recoverable from the
realized grid, and exhaustively tested in representative dimension combinations.

**Reason/evidence:** the baseline override stage produced thousands of mismatch,
self-check, and generation findings; the final override report accepts
64,620/64,620 draws with no findings. Retained reports:
`checks/before/checks/7b0c20fe6f33_before_override_results.json` and
`checks/after/checks/7b0c20fe6f33_after_override_results.json`.

**Rejected alternative:** keep compatibility aliases for old decorative keys.
That would preserve silently inert controls and make the public contract less
truthful. Unknown keys now fail loudly.

## D2. Cover canonical scale and broaden the semantic domain

**Prior choice:** exactly four green cells and only vectors `(1,2)`, `(2,1)`,
`(-1,2)`, `(2,-1)`. Canonical examples instead contain a three-cell L and
vectors `(4,5)`, `(-4,3)`, and `(5,1)`.

**New choice:** 11 connected motifs of sizes 3–5 and 16 vectors combining
canonical, legacy, sign-varied, and cardinal displacements. Dimensions span
9–16, while scheduled canonical slots emit 10×10, 11×11, and 12×12 profiles.

**Reason:** training data must include the canonical regime while defeating the
shortcut “always four cells moved by a small knight vector.” The profile-floor,
diversity, semantic, and grammar stages are all green after the change.

**Rejected alternatives:**

- sampling arbitrary disconnected cells, because that stops teaching “copy the
  whole object” and introduces accidental source/target overlap;
- only reproducing canonical examples, because three fixed vectors and one motif
  leave severe shortcut support;
- an unrestricted polyomino/vector generator, because it adds placement failure
  modes without evidence that the extra complexity improves this task.

## D3. Use a four-position witness schedule but require only three demos

The schedule is `canonical`, `extended`, `legacy_bridge`, `cardinal`. Each
three-of-four subset contains evidence against all three declared rivals:
`legacy_knight_only`, `copy_first_three`, and `filled_bounding_box`.

This supports normal ordered lessons and arbitrary query rotation. The required
semantic gate checked 48/48 rotations; the larger source-bound census checked
1,200/1,200 rotations across 300 lessons. Evidence:
`checks/after/checks/7b0c20fe6f33_after_semantic_gate.json` and
`checks/lesson-census.json`.

**Limitation:** this establishes identifiability only against the named rivals
and hook validation, not all possible hypotheses.

## D4. Keep only constructive valid inputs

Negative examples `no_marker_pair`, `no_3_cells`, and `copy_out_of_bounds` were
removed from the advertised valid texture domain. They are useful validator
tests, not training inputs for an executable rule that presupposes a marker pair
and a translatable object. Malformed near-misses are now covered by focused unit
tests instead.

## D5. Synchronize duplicate authority text without changing semantics

The selected base record's `target_code` differed from its own `raw_code` only by
two explanatory comments. `target_code` now equals `raw_code`, making all active
authorities exact-text synchronized. No Racket expression, rule hash, canonical
output, or behavior changed. Authority-sync and execution parity pass.

## D6. Self-review for newly introduced shortcuts

I checked motif size, rectangularity, vector family/sign, grid profile, uniqueness,
and every query rotation. A small witness is any scheduled `extended` sample:
its four- or five-cell nonrectangular motif with a long vector simultaneously
refutes “copy first three,” “fill the bounding box,” and “legacy vectors only.”
The remaining restriction is explicit rather than hidden: support is finite to
11 motifs and 16 vectors.
