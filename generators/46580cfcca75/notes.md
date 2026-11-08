# Working notes: 46580cfcca75

## Review repair

The imported `2.0.0` generator was far outside canonical scale (12–21 rows vs.
canonical 6–8), omitted `RULE_HASH` and `self_check`, advertised dead palette,
texture, density, and color-count controls, silently accepted unknown overrides,
and had no executable lesson contract.

The `3.0.0` repair keeps the authoritative rule unchanged and narrows generation
to the task's observed solid-rectangle manifold. Defaults cycle through the four
canonical size/color-count profiles. Two of four residues contain a thin second
rectangle, three contain multiple objects, and every residue contains a rectangle
with an erasable interior; therefore any three-example rotation refutes all four
declared competitors.

Difficulty changes rectangle-area bands, positions, and palettes while preserving
the same semantic support. Explicit public controls always win and remain legal
in every band. The full-grid one-color impostor is rejected by requiring visible
background zero.

## Reusable probes

- `workspace/reference_oracle.py`: independent connected-component/bbox oracle.
- `workspace/lesson_probe.py`: source-bound consecutive-window census that loads
  the live rival/witness declarations and checks every query rotation.

## Limits

The ordinary domain intentionally contains only one or two distinct-color solid
rectangles. It does not teach arbitrary nonrectangular objects, touching objects,
three-plus objects, repeated colors, or malformed inputs, even though the Racket
program may execute some of them. Finite rival checks do not prove unique rule
induction against undeclared programs.
## Current reviewer considerations

Source SHA-256: `6580efc42ec00d017ce240022a738d4fa0520ab3f79784bd9b13abc9465d4185`.

# Decisions: 46580cfcca75

## D1 — Preserve the selected Racket authority

**Input choice.** Keep the canonical program unchanged and pin
`RULE_HASH = "001f318153f4"`.

**Original rationale.** The rule and all four canonical labels were internally
consistent; the defect was in sampling and metadata, not label authority.

**Alternatives considered.** Broaden or rewrite the rule to apply only to filled
rectangles, or alter it to ignore nonrectangular components. Both would silently
change an authoritative ARC task and were unnecessary.

**Probes.** Authority sync, Racket lint, 120-application rule smoke, 4/4 canonical
oracle parity, and 120/120 independent Python-mirror parity.

**Failure modes and limits.** The Python mirror is a transcription and does not
replace Racket authority. Any later canonical program change invalidates the pin.

## D2 — Keep the generated domain on solid rectangles

**Input choice.** Ordinary inputs contain one or two distinct-color filled
rectangles, separated by at least one background row or column. At least one is
3×3 or larger; some lessons also contain a 2-cell-thick rectangle.

**Original rationale.** Every canonical object is a solid rectangle. The imported
generator stated this domain but sampled much larger scenes and included unlawful
negative textures.

**Alternatives considered.** Generate arbitrary connected blobs because the
Racket program outlines any component's bounding box. That would broaden the
program domain but no longer match the task's demonstrated concept. Generate
only large rectangles; rejected because it leaves the plausible `drop_thin`
shortcut untested.

**Probes.** Canonical acceptance, structural `self_check`, independent object
oracle, semantic witness counts, and task tests over 480 default draws plus exact
override corners.

**Failure modes and limits.** Models trained only here are not explicitly taught
nonrectangular objects, touching objects, or repeated colors.

## D3 — Replace nine decorative controls with three exact axes

**Input choice.** Retain only `grid_h`, `grid_w`, and `n_rects`. Their full domain
is 6..14 × 7..16 × 1..2, with no incompatible combinations.

**Original rationale.** Unknown. The baseline declared palette kind/size,
position bias, distinct-color count, density, and texture despite ignoring or
collapsing them. The before override check produced thousands of findings and
accepted unknown keys.

**Alternatives considered.** Implement every legacy alias. This adds complexity
without a distinct visible semantic and preserves misleading metadata. Keep
single-value axes as diagnostics; rejected because they are not useful controls.

**Probes.** Exact corner tests in every band, malformed-type and unknown-key tests,
`observe_overrides` round trips, and the 13,680-draw repository override gate.

**Failure modes and limits.** This intentionally breaks callers relying on
previously nonfunctional axis names; version was bumped from 2.0.0 to 3.0.0.

## D4 — Anchor every default draw to a canonical profile

**Input choice.** Cycle through `(6,8,2 objects)`, `(7,7,2)`, `(7,9,2)`, and
`(8,9,1)` by `sample_index mod 4`.

**Original rationale.** The imported default range could never reproduce a
canonical grid profile and failed both exact and envelope coverage 0/60.

**Alternatives considered.** Assign a nonzero random probability to canonical
sizes. A deterministic cycle gives a hard coverage guarantee and makes cyclic
lesson analysis cheap. Restrict all explicit overrides to canonical sizes;
rejected because modest scale generalization is useful.

**Probes.** Profile floor 60/60, schedule-profile tests, 400-window task-local
probe, and production lesson census.

**Failure modes and limits.** The period is deterministic. Sample index must not
be exposed as a model feature; the grid itself carries no schedule marker.

## D5 — Require three demonstrations and two copies of fragile witnesses

**Input choice.** `EXAMPLES_NEEDED = 3`. In each four-sample period, two slots
contain a thin second rectangle, three contain multiple objects, and all four
contain an erasable interior.

**Original rationale.** One thin slot would teach the intended rule in one query
ordering but allow a `drop_thin` rival whenever that sole witness became the
query. One copy is therefore insufficient under arbitrary query rotation.

**Alternatives considered.** Use four demonstrations, random witness frequency,
or forbid rotations. Three demonstrations match the task's modest complexity;
two deterministic witness slots provide the needed leave-one-out redundancy.

**Probes.** Every query rotation for every four-slot start in tests; 1,200 official
census rotations; 1,600 independent cyclic-probe rotations.

**Failure modes and limits.** The finite rival set is task-derived, not complete.
An undeclared conditional rule may still fit finite examples.

## D6 — Declare executable rivals and witnesses

**Input choice.** Rivals are `identity`, `largest_only`, `drop_thin`, and
`global_bbox`. Witnesses are interior erasure, multiple objects, and a thin
rectangle, each bound to the rivals it should refute.

**Original rationale.** The baseline comments named informal shortcuts but had no
executable contract, so no automated lesson-level evidence existed.

**Alternatives considered.** Add generic transformation search or many synthetic
rivals. A compact set derived directly from visible ambiguities is cheaper,
interpretable, and maintainable.

**Probes.** Semantic gate witness claims, `lesson_identifiable`, canonical/task
oracle tests, official lesson census, and `workspace/lesson_probe.py`.

**Failure modes and limits.** Passing declared rivals does not establish unique
induction over all possible programs.

## D7 — Make difficulty visible without removing semantics

**Input choice.** Easy/medium/hard use different area-ranked rectangle choices,
positions, and palette RNG streams. Every band retains the same profiles and all
semantic witness slots.

**Original rationale.** The first repair made bands byte-identical, which defect
lint correctly flagged. Difficulty should alter visible data, not merely metadata.

**Alternatives considered.** Give easy no thin objects or only one rectangle;
rejected because an entire band would train a weaker rule. Change grid sizes by
band; rejected because every band must retain canonical-profile support.

**Probes.** Regression test comparing same seed/sample across bands, final defect
lint, per-band profile floor, per-band semantic witness counts, and 100 lessons
per band.

**Failure modes and limits.** Difficulty is geometric heuristic, not calibrated
against Qwen3.5-9B error rates.

## D8 — Use constructive placement instead of retry-and-drop

**Input choice.** Enumerate feasible horizontal/vertical dimension layouts, then
choose and place one. The minimum 6×7 canvas always fits two 3×3 rectangles with
a one-column gap.

**Original rationale.** The baseline retried random boxes and could silently
return fewer rectangles than requested, even returning `[[0]]` if placement
failed.

**Alternatives considered.** Increase retry counts or declare incompatible small
canvases. Both leave probabilistic failure or unnecessary holes in the public
Cartesian product.

**Probes.** Exhaustive domain-corner tests across bands and the full override
matrix; `self_check` is asserted inside `generate` as a final loud guard.

**Failure modes and limits.** The dimension family is intentionally bounded to
height ≤5 and width ≤6 for legibility even on larger canvases.

## D9 — Reject the full-grid one-color impostor

**Input choice.** Require at least one visible background-zero cell in addition
to rectangle structure and an erasable interior.

**Original rationale.** An intermediate validator accepted a full grid of one
color; defect lint's `selfcheck-minimal-impostor` probe exposed this.

**Alternatives considered.** Require a full one-cell margin around every object.
Rejected because canonical rectangles may touch a grid edge. Require a minimum
background fraction; unnecessary and more arbitrary.

**Probes.** Dedicated failing-then-passing regression test and final defect lint.

**Failure modes and limits.** Very dense but still lawful grids remain accepted as
long as a zero exists and other structural conditions hold.

## D10 — Add independent reusable review tools

**Input choice.** Keep `workspace/reference_oracle.py` independent of the selected
generator and add `workspace/lesson_probe.py`, which discovers live rival/witness
declarations and checks consecutive starts plus every query rotation.

**Original rationale.** The shared census samples production starts but explicitly
does not enumerate every cyclic start. This task has a small deterministic period,
so exhaustive schedule testing is cheap and valuable.

**Alternatives considered.** Rely only on pytest fixed cases or duplicate rival
names inside the probe. Fixed cases under-sample the schedule; copied names drift.

**Probes.** The probe itself is covered by task tests and its final 100-per-band
run produced 400 windows, 1,600 rotations, 1,564 unique inputs, and 0 failures.

**Failure modes and limits.** The independent oracle may contain a transcription
error, so final labels still come from Racket. Finite starts/seeds remain finite.
