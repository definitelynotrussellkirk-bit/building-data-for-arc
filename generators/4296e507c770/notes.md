# Working notes: 4296e507c770

## Review repair, 2026-10-04

Baseline generator SHA-256:
`26e168cbe8c5cff757f360224308018ad3dd31f3fe7b083037aa68aedc5a9705`.
Final generator SHA-256:
`fb9820c5106d63e1c53cad96c86a9eaede41fe0a14924fbc423de9ddf2586248`.
The canonical Racket authority was not changed; `RULE_HASH` is pinned to
`6c9be515e84b`.

The imported generator advertised shape, marker, palette, position, and texture
variation but ignored most controls, accepted unknown controls, generated no
canonical-sized profiles in the measured baseline sample, and declared no
executable lesson rivals.  It could omit transform codes or use symmetric
shapes, allowing a lesson to carry correct labels without teaching the complete
code map.

Version 3.0.0 keeps only four genuine exact axes (`grid_h`, `grid_w`,
`template_size`, `n_markers`).  It schedules both canonical profiles and one
broad profile in a stable three-cycle.  Every ordinary sample contains all four
marker codes and an exact-size connected shape whose identity, left/right,
up/down, clockwise, and counterclockwise signatures are pairwise distinct.
Marker placement reserves room for every relevant transform, not merely the
assigned transform, so all declared rivals are total on the generated domain.

The initial correct-by-contract layout search shuffled every legal anchor and
made the exhaustive 33,390-draw override stage exceed its 300-second stage
budget.  The final implementation uses bounded randomized placement with a
deterministic exhaustive fallback.  Measured generation plus `self_check`
averaged about 1.0 ms/draw over 1,000 draws; the complete override stage then
passed all 33,390 draws.

Retained independent tools:

- `workspace/reference_probe.py`: geometry-derived oracle, canonical check,
  deterministic/diversity census, declared-rival checks, and sampled Racket
  parity.
- `workspace/lesson_rotation_probe.py`: tests every member of each lesson as the
  query and records competitor exceptions as failures rather than treating a
  partial function as a refutation.

Limits: the finite rival set does not prove universal identifiability; templates
are intentionally bounded to 4×4 and use the canonical palette/output color.
The broad profile varies dimensions, size, count, shape, and placement, while
canonical profiles remain frequent enough for transfer.
## Current reviewer considerations

Source SHA-256: `fb9820c5106d63e1c53cad96c86a9eaede41fe0a14924fbc423de9ddf2586248`.

# Decisions — `4296e507c770`

## D1 — Replace, rather than patch, the baseline generator flow

**Input evidence.** The before battery had three blocking stages (`lint`,
`defect_lint`, `override`) and two advisory stages.  The override report found
76,386 issues over 73,440 draws; most advertised controls were ignored and an
unknown key was accepted.

**Decision.** Preserve the canonical task and Racket authority, but rewrite the
task-local generator around an explicit lawful model.

**Rejected alternative.** Keeping the old palette/position/texture fields and
special-casing the gate would preserve misleading public controls and make
future lesson composition depend on accidental behavior.

## D2 — Expose only four exact axes

The retained axes are `grid_h=12..22`, `grid_w=14..24`,
`template_size=4..9`, and `n_markers=4..6`.  Each is directly observable and
every declared boundary cross-product is constructible.  Unknown axes,
non-integers (including booleans), and out-of-range values raise `ValueError`;
`None` follows the shared unset convention.

Palette variation was rejected because the canonical semantics assign meaning
to colors 2–6 and output color 8.  A nominal `position_bias` axis was rejected
because there was no second meaningful policy.  “Degenerate textures” were
removed from the ordinary lawful domain instead of being advertised as data.

## D3 — Schedule canonical transfer support explicitly

A stable three-cycle emits `canonical_12`, `canonical_13`, and `broad` profiles.
The canonical profiles use 12×18 or 13×18 grids, a five-cell template, and one
marker of each code.  The broad profile varies dimensions, exact shape size,
marker count, shape, and placement by difficulty.

A purely broad random sampler was rejected because the baseline had zero exact
canonical-profile hits.  An all-canonical sampler was rejected because it would
restore narrow memorization pressure.

## D4 — Make every individual example teach the code map

Every ordinary example includes marker colors 3, 4, 5, and 6.  Templates are
connected, exact-size, bounded to 4×4, and required to have five distinct
signatures: identity, left/right reflection, up/down reflection, clockwise
rotation, and counterclockwise rotation.

Allowing symmetric templates or optional code colors was rejected.  Such inputs
can be lawful, but they let plausible wrong rules agree with the label and shift
the burden unpredictably to lesson assembly.

## D5 — Require rival totality at placement time

The first green attempt revealed that a marker could fit its assigned transform
but place a rival transform out of bounds.  The final placement reserves room
for all five relevant template variants at every marker.  This makes declared
rivals total and prevents “exception means refuted” from inflating semantic
coverage.

The alternative—catching rival exceptions in the gate only—would expose a bad
contract but leave the generator domain unnecessarily brittle.

## D6 — Keep outputs noninterfering and markers isolated

Intended stamp footprints are pairwise disjoint; marker cells are isolated and
cannot land inside another output footprint; the source template is separated
from markers and output footprints.  This removes overwrite-order and marker
occlusion ambiguities without changing the task's core rule.

## D7 — Add executable semantic contracts

The generator declares three plausible competitors:

1. ignore marker colors and stamp identity everywhere;
2. swap the horizontal and vertical mirror mappings;
3. rotate color 6 counterclockwise.

Three witnesses map directly to those errors.  `lesson_identifiable` reports a
competitor only when it fits all demonstrations and changes the query.  No
canonical shortcut is declared because all three rivals are already refuted by
each canonical pair.

These rivals are high-value but finite; they are not presented as a proof of
universal induction.

## D8 — Keep Racket as authority; use Python only for probes

The canonical Racket program was unchanged.  `RULE_HASH` is pinned to
`6c9be515e84b`.  The Python mirror exists only for validation, rivals, and cheap
lesson probes.  A separate geometry oracle in `reference_probe.py` was written
without calling the production mirror, then sampled against Racket (39/39).

Changing the Racket rule was rejected because canonical examples and authority
smoke tests were already correct.

## D9 — Optimize placement without narrowing the contract

The first complete override attempt hit the stage's 300-second cap.  Profiling
showed that repeatedly shuffling every legal anchor dominated runtime.  The
final layout algorithm uses bounded random candidate sampling, retries whole
layouts, and retains deterministic exhaustive search as a safety fallback.

Reducing the override domain or declaring artificial incompatibilities was
rejected.  Generation plus `self_check` measured about 1.0 ms/draw after the
change, and the unchanged 33,390-draw contract passed.

## D10 — Retain independent, reusable probes

`reference_probe.py` checks canonical examples, independent geometry, replay
determinism, diversity, transform separation, rival disagreement, and sampled
Racket parity.  `lesson_rotation_probe.py` materializes consecutive lesson
windows, rotates every pair into the query slot, consumes the actual declared
competitor dictionary, and fails on competitor exceptions.

The stock production census was still run at 100 lessons per band.  The local
cyclic probe supplements it rather than replacing its source-bound Racket labels.

## Known limits

The generator does not vary semantic colors, template bounding boxes beyond
4×4, or the output color.  It tests three named rivals, not all possible rules.
The cyclic audit uses an independent Python oracle after separate sampled Racket
parity, which is the cheapest reliable division of labor but not a Racket call
for every rotated pair.

## D11 — native modal transform-composition family (review-d54ac4e249fb35e7)

The retained task-local family adds one episode-fixed parameter,
`stamp_rule=direct|modal_postcompose`. `direct` returns the selected canonical
Racket program byte-for-byte. `modal_postcompose` counts colors 3–6, interprets
the unique repeated marker color as a global transform, applies each marker's
local transform first, then post-composes the counted transform before stamping.
This preserves the original template/marker reasoning while adding a genuine
count → transform selection → composed stamping dependency.

Ordinary seeds vary connected full-D4-orbit template geometry, safe six-slot
layout, and marker order independently of the private setting. Stable prefixes
support 2–6 demonstrations and 1–4 queries. The fourth query is a substantive
30×30 boundary case. A finite audit rejects the other admitted setting plus
`global_only`, reversed composition, three fixed-global rules, and first/last
marker shortcuts using demonstrations only. The retained protected-Racket audit
executed 63 labels; a 64-seed construction/certificate sweep covered 384
episodes, 2,944 pairs, and 577 distinct inputs.

Native qualification at three demonstrations and four queries passed both
settings on seeds 20261024 and 17: four jobs and 40 protected-Racket evaluations.
The source-bound wrong-intermediate witness changes the counted color from 4
(left/right reflection) to 6 (clockwise rotation) and changes the final grid.
Evidence is under `workspace/parametric/evidence/`,
`WORK/checks/4296e507c770/qualification/`, and
`WORK/checks/4296e507c770/causal/`. This is reviewer-ready and owner-pending;
there is no owner acceptance or training admission, and the finite rivals do
not prove universal identifiability.
