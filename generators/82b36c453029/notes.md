# Current notes: `82b36c453029`

## Intended rule and authority

On a 0-background grid, find each same-color 4-connected nonzero component.
Return a fresh 0-canvas of the same shape with one same-color cell per component
at `((r1+r2)//2, (c1+c2)//2)`, where `(r1,c1,r2,c2)` is that component's tight
bounding box. Canonical `RULE_HASH` is pinned to `b5f364e5c32b`; the Racket
reference and canonical rows were not changed in review
`review-a2428c582fd4e026`.

## Generator domain

Version `3.0.0` constructs 7..14 by 9..16 grids containing exactly 3..4 isolated
component boxes and exactly 2..3 foreground colors. Components use a finite
shape library: canonical solid 3×3, 1×3, 3×1, 1×5, and 5×1 rectangles; an
asymmetric 2×4 witness; a hollow 3×3 ring; and a plus. Disconnected components
may share a color. Component bbox centers must be distinct.

Public exact axes are only `grid_h`, `grid_w`, `components`, and
`n_distinct_colors`. Accepted overrides are strict and observable through
`observe_overrides`; there are no declared incompatible combinations.

## Teaching schedule

`EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 3`. Production alternates:

1. `canonical` — three distinct-colored canonical solids;
2. `witness_a` — four objects/two colors with every decisive witness;
3. `witness_b` — three objects/two colors with every decisive witness.

Any three demonstrations left after holding one query out of four consecutive
samples retain a witness profile. Fixed-seed enumeration across all three bands
checked 9 lessons/36 rotations with zero ambiguity; a 100-per-band census checked
300 lessons/1,200 rotations with zero ambiguity. These are finite declared-rival
results, not proof against every possible hypothesis.

## Canonical shortcuts and witnesses

The canonical pairs also fit four wrong rules, so the generator declares and
actively refutes them:

- one center per color → repeated-color disconnected components;
- nearest cell centroid → asymmetric component;
- upper/ceiling bbox midpoint → even bbox requiring floor tie-break;
- paint only an occupied center → hollow-center ring.

The exact legal multi-rival counterexample is
`counterexamples/canonical-shortcuts/manual-witness.json` and is covered by
`tests/test_generator.py::test_exact_manual_counterexample_refutes_all_declared_shortcuts`.

## Decision reversal from `2.0.1`

The prior generator advertised nine axes, sampled only isolated solid rectangles,
accepted negative textures in the ordinary domain, and used a broad
shape-only `self_check`. The fresh baseline battery found missing `RULE_HASH`,
0/56 destructive mutations rejected, 26 defect-lint warnings, and 6,917 override
findings. Those choices were replaced rather than patched with aliases:

- misleading palette/texture/density/position axes were removed;
- rejection sampling was replaced by constructive box placement;
- exact control ranges were narrowed to guaranteed support;
- canonical solids were retained, while scheduled asymmetric/hollow/repeated-
  color cases were added;
- `self_check`, rule mirror, rivals, witnesses, and lesson hook became executable.

Evidence is retained under `WORK/checks/`; final generator SHA-256 is
`8ff3bc682ff09dc7efea039ae84ef5f36f1054c1a47cf84e8e56c9368d9e5c3d`.

## Known limits and open findings

The generator intentionally does not cover every component shape or every grid
on which the authority is defined. Expanding the shape library is reasonable,
but each addition must preserve exact placement/override guarantees and should
be checked against current and new rivals across the complete lesson schedule.
No selected-task blocker remains in this review; training approval remains a
maintainer decision and was not changed by passing checks.
## Current reviewer considerations

Source SHA-256: `8ff3bc682ff09dc7efea039ae84ef5f36f1054c1a47cf84e8e56c9368d9e5c3d`.

# Decisions for `82b36c453029`

## D1 — Keep the canonical authority unchanged

**Prior choice:** the baseline prose described the correct bbox-center rule but
did not pin it with `RULE_HASH`.

**Decision:** retain the canonical Racket law and pin
`RULE_HASH = "b5f364e5c32b"`. Add an independent Python mirror for tests and
semantic probes; do not edit canonical data.

**Alternatives considered:** changing the rule to centroid, requiring the center
to be occupied, or treating color as object identity. All fit the canonical
examples but are not the selected authority.

**Probe/evidence:** all five canonical inputs are accepted and the mirror equals
the canonical outputs; `rule_smoke`, `racket_lint`, and `authority_sync` are green
in `checks/after/checks/82b36c453029_after_battery_summary.json`.

**Failure mode / limit:** the mirror is supporting code, not a second authority.
The Racket result remains decisive.

## D2 — Replace nine advertised axes with four exact observable controls

**Prior choice:** `grid_h`, `grid_w`, `palette_kind`, `components`,
`palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`
were advertised. Most semantic/palette controls were ignored, one-token, aliases,
or mixed ordinary and negative fixtures; dimensions also declared much wider
ranges than production reached.

**Decision:** expose only `grid_h` 7..14, `grid_w` 9..16, `components` 3..4,
and `n_distinct_colors` 2..3. Every accepted value is exact and recoverable by
`observe_overrides`; bad scalar types, unknown keys, and out-of-range values are
rejected.

**Alternatives considered:** preserve legacy axis names with many incompatibility
rules; keep textures as diagnostics; or silently clamp difficult combinations.
Those options leave a misleading public API and make the override matrix hard to
reason about.

**Probe/evidence:** task tests exercise exact joint controls across all bands;
final `override` is green. Baseline failures are in
`checks/before/checks/82b36c453029_before_override_results.json`.

**Failure mode / limit:** the smaller control domain is deliberate. It trades
breadth for exactness and does not expose arbitrary shape selection.

## D3 — Use constructive shape-aware placement

**Prior choice:** up to 500 rejection-sampling attempts placed random solid
rectangles, with no proof that the requested count was achieved and independently
sampled colors that could merge same-color adjacent rectangles conceptually.

**Decision:** choose shapes first, backtrack over their actual bounding boxes,
and require at least one blank row or column between every pair of boxes. This
guarantees the exact component count and keeps output centers distinct.

**Alternatives considered:** retain retry sampling with a final validator; use a
fixed layout template; or allow touching same-color components. Retry sampling
can fail exact controls, a single template hurts diversity, and same-color
contact destroys component identity.

**Probe/evidence:** 41 task tests, final override gate, diversity gate, and
self-check all pass.

**Failure mode / limit:** extreme dimensions/counts outside the declared ranges
are rejected rather than approximated.

## D4 — Preserve canonical support but schedule decisive counterexamples

**Prior choice:** production used only isolated solid rectangles, generally with
one component per color. Canonical examples therefore supported several wrong
rules.

**Decision:** use a period-3 profile schedule:

1. `canonical`: three distinct-colored solid odd rectangles at canonical sizes;
2. `witness_a`: four objects, two colors, including an asymmetric 2×4 footprint
   and a hollow 3×3 ring;
3. `witness_b`: three objects, two colors, with the same decisive geometry.

Both witness profiles contain every geometric witness. Repeated colors force
object-level rather than color-level processing.

**Alternatives considered:** random witness frequency without a schedule; one
large combined witness in every sample; or remove canonical profiles entirely.
Random frequency does not guarantee each lesson teaches the rule, an always-on
super-witness narrows surface variety, and dropping canonical profiles would
lose direct source support.

**Probe/evidence:** fixed-seed period enumeration is 9/9 production lessons and
36/36 rotations identifiable; the wider census is 300/300 lessons and
1,200/1,200 rotations identifiable. Evidence:
`checks/lesson-census-schedule-s0.summary.json` and
`checks/lesson-census-100-per-band.summary.json`.

**Failure mode / limit:** this deterministic period is part of the teaching
contract. Reordering or changing `EXAMPLES_NEEDED` requires a new exhaustive
schedule receipt.

## D5 — Declare four canonical-fitting rivals and pair them with witnesses

**Decision:** retain executable rivals for:

- `one_center_per_color` ↔ repeated-color disconnected objects;
- `nearest_cell_centroid` ↔ asymmetric shape;
- `upper_bbox_midpoint` ↔ even bbox requiring floor tie-breaking;
- `occupied_center_only` ↔ hollow-center ring.

The same functions are exposed through `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; witness predicates are pure and
tested.

**Alternative considered:** rely only on generic shared rivals. Generic checks
are useful but do not express these task-specific canonical ambiguities.

**Probe/evidence:** the exact legal witness in
`repo/generators/82b36c453029/counterexamples/canonical-shortcuts/manual-witness.json`
refutes all four, and Racket output is retained at
`checks/selected-shortcut/authority.json`.

**Failure mode / limit:** passing a finite rival set does not prove unique human
induction. New plausible shortcuts should be added to the executable contract.

## D6 — Make `self_check` a grammar validator, not an acceptance stub

**Prior choice:** the validator checked only nonempty rectangular shape and broad
dimensions; it rejected 0/56 destructive mutations.

**Decision:** validate literal ARC cells, exact dimension/color/component ranges,
allowed normalized shapes, and distinct bbox-center outputs. Accept all five
canonical inputs and all generated profiles.

**Alternative considered:** accept every grid on which the Racket rule can run.
That would be a rule-domain validator, not a truthful generator-domain contract.

**Probe/evidence:** final `selfcheck` and `defect_lint` are green; tests include
malformed grids and structural impostors.

**Failure mode / limit:** lawful authority inputs outside the finite shape
library can be rejected. That is documented generator scope, not a statement
that the authority is undefined there.

## D7 — Retain interrupted evidence and resume only unchanged sources

**Decision:** preserve the first final-battery attempt as interrupted and resume
from its checkpoint with the same generator and schedule-census hashes. Do not
present the partial run as a pass.

**Evidence:** `checks/after-command.log`, `checks/after/attempts/0001/`,
`checks/after-resume-shell.log`, and the completed battery summary.

**Limit:** the interruption was a caller/runtime transport event, not a measured
stage failure. It motivates shared-tool feedback F1 but does not weaken the final
source-bound result.

## D8 — Audit targets remain unchanged

The two randomly assigned audit targets were inspected adversarially after the
selected repair. I added only evidence under `checks/audit/`; no target source
was edited. Details and exact reproductions are in `AUDIT.md`.
