# Working notes: 725513c9d0c9

## 2026-10-03 review `review-2017bc62d7231b33`

Lead used: retained return `local-random-7c924b0c34af` from
`evidence/associated_notes.jsonl`. Its component-isolation, cardinal-adjacency,
and four-example semantic-window repairs were present in the pinned baseline and
were remeasured rather than assumed. The required before battery was all green.

Two independent distribution shortcuts remained despite that green baseline:

1. Every profile assigned palette role 0 to the target, and all four declared
   palettes were numerically sorted. A marker-free selector choosing the
   component with the smallest color (breaking ties by more distinct colors)
   selected the target in every sampled baseline lesson window. Version 3.3.0
   rotates role-to-color assignment by sample index; residue 2 guarantees a
   non-minimum-color target in every four-example window.
2. Every profile had a unique canvas size, and that size uniquely identified the
   target D4 morphology. A marker-free dimension-to-shape lookup therefore fit
   every baseline generated pair and every canonical pair. Version 3.3.0 uses a
   cross-profile canvas on residue 3, reusing 12x14 and 14x16 canvases across
   unrelated target morphologies while keeping canonical dimensions in the other
   slots.

Both shortcuts are now executable `SEMANTIC_RIVALS` with linked witnesses, so
semantic checks and lesson census runs can detect regressions. The Racket rule
and `RULE_HASH = d635ca555626` are unchanged because the repair affects only the
input distribution and its Python-side semantic contract.
## Current reviewer considerations

Source SHA-256: `e89c7caace24c4732945d75ee99e1886afd4e19298aabec30ad483f813b7490a`.

# Decisions: 725513c9d0c9 review

## D1 — retain the existing semantic rule and authority

**Original rationale.** The retained lead had already repaired component
isolation and cardinal marker adjacency. The pinned baseline passed all 12
stages, canonical outputs, authority synchronization, and real Racket smoke.

**Choice.** Leave the Racket authority and `RULE_HASH = d635ca555626` unchanged.
The reproduced defects were properties of the input distribution, not of the
transformation.

**Rejected alternatives.** Rewriting the Racket source, changing canonical
examples, or redefining the target would add authority risk without addressing
the shortcuts. Evidence: before and after authority-sync reports under
`checks/before/checks/` and `checks/after/checks/`.

## D2 — deterministic palette-role rotation

**Original state and rationale.** Each profile used semantic palette roles and
role 0 was the target. The palettes happened to be sorted numeric tuples; no
recorded rationale justified making numeric rank predict the target.

**Choice.** Rotate the selected palette tuple by
`sample_index % needed_colors`. This preserves the palette membership and every
palette override while changing role ownership deterministically. Residue 2 of
the four-slot schedule has four roles, so every cyclic four-example window
contains a target that is not selected by the smallest-color rival.

**Alternatives considered.** A random shuffle was rejected because a complete
lesson could still accidentally preserve the shortcut and because regressions
would need probabilistic thresholds. Assigning a separately sampled color per
component was rejected because it could violate exact palette semantics or
create duplicate roles. Reordering profile components was rejected because it
would conflate layout and color leakage.

**Probe.** `test_every_four_example_window_breaks_palette_rank_selection`
checks all 12 cyclic starts in each of three bands. Red and green evidence:
`checks/red-palette-rank/result.json` and
`checks/green-palette-rank/result.json`.

## D3 — cross-profile canvas reuse in one schedule slot

**Original state and rationale.** Canonical profiles intentionally preserved
published dimensions, but every profile had a unique size. Dimensions therefore
acted as a morphology label even though they are irrelevant to the rule.

**Choice.** Split profile recognition into a morphology signature and a full
strict signature. Keep canonical dimensions on residues 0–2; on residue 3,
choose a roomy canvas from `(12,14)` or `(14,16)` other than the profile's
original size. This breaks dimension-to-shape lookup while retaining frequent
strict-canonical draws.

**Alternatives considered.** Fully random dimensions were rejected because
placement feasibility would become a broad new failure surface and strict
canonical support would fall unnecessarily. Adding many new dimensions was
rejected as YAGNI after two shared sizes supplied direct counterexamples.
Changing target morphology instead of dimensions was rejected because fixed
morphologies were not the reproduced leak; their one-to-one association with
canvas size was.

**Probe.** `test_canvas_dimensions_do_not_label_one_target_shape` forces every
profile through the flexible slot in every band and requires at least one canvas
size to host multiple target D4 signatures. Red and green evidence:
`checks/red-canvas-shape/result.json` and
`checks/green-canvas-shape/result.json`.

## D4 — make both shortcuts executable contracts

**Choice.** Keep `palette_rank_selector` and `dimension_shape_lookup` as actual
functions and expose them through `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and
`CANONICAL_SHORTCUTS`; add linked semantic witnesses. This lets the battery and
source-bound census replay the same hypotheses rather than relying on prose.

**Rejected alternative.** A one-off regression assertion alone would protect the
current schedule but would not give the shared semantic gate or lesson census a
rival to score. Copying separate rival implementations into tests was rejected
to avoid divergence.

**Probe.** Contract tests first failed, then passed; final semantic and census
reports are `checks/after/checks/725513c9d0c9_after_semantic_gate.json` and
`checks/lesson-census.json`.

## D5 — no procedural profile rewrite

A procedural shape grammar could provide broader morphology support, but it
would be an architectural change rather than a targeted repair. The current
fixed profiles already provide multicolor targets, disconnected color reuse,
diagonal decoys, bbox intruders, size-order counterexamples, sparse holes, and
canonical support. With both reproduced shortcuts directly broken and all final
gates green, a wider rewrite was deferred.

## Failure modes and limits

- Palette rotation is periodic and visible through lesson order. The tests show
  that the simple numeric-rank rival fails; they do not rule out every joint
  schedule-and-profile classifier.
- Flexible dimensions are limited to two roomy sizes and one residue. This is
  enough to break a dimension-only lookup but not every high-complexity lookup.
- Morphology recognition assumes the finite profile signatures remain unique.
  The selected tests exercise every current profile and exact overrides; adding
  a profile requires rerunning collision checks.
- The census rotates consecutive lesson starts but does not rotate every pair
  into the query position. The task-local cyclic-window test covers all starts
  of the deterministic four-slot schedule, while the census supplies 300
  source-bound production lessons.
- Finite declared-rival evidence is not a proof of induction. These limitations
  are nonblocking because no surviving rival or failed final check was observed.
