# Working notes: 5f5b990b28ab

## Baseline diagnosis

The selected v2.1.0 baseline generated only concentric frames.  That made the
intended bbox-area ranking observationally equivalent to several shortcuts on
all generated examples.  It also omitted the canonical `RULE_HASH`, advertised
four texture controls that never changed a grid, silently accepted unknown
controls, and had an overlapping-axis warning.  The before battery retained in
`checks/before/` had 7 green stages, 2 advisory stages, and 3 failures (lint,
defect lint, and override).

A supported Racket `apply` probe in `workspace/probes/authority_inputs.json`
confirmed that lawful objects need not be concentric and that the selected rule
ranks disconnected components by bbox area.  Its three main boxes have areas
30, 28, and 27 while scan order, perimeter/cell count, and width disagree.

## v3.0.0 design

* Pin `RULE_HASH = d23e43212061`; do not alter the authoritative Racket rule.
* Replace dead/overlapping axes with one exact observable axis,
  `scene_profile`.
* Cycle through five profiles: canonical nested-3, area-stress-3, nested-2,
  area-stress-4, nested-4.
* Put both disconnected stress roles in every five consecutive samples, so any
  four-demo/one-query rotation retains at least one decisive witness.
* Declare executable rivals and witnesses for scan order, perimeter/cell count,
  and bbox width.
* Reject unknown or invalid overrides and malformed grids with diagnostics.
* Keep an independent oracle and real-Racket parity helper in
  `workspace/reference_probe.py` for future reviewers.

## Verification snapshot

Final generator SHA-256:
`118d51fde17615f49b93040afce0bef735df4537c9074d23e694b2bd42d7f623`.

* Task-local TDD suite: 42 passed.  The retained red run had 34 failures and 8
  passes before implementation.
* Final after battery: 12/12 stages green.
* Strict semantic gate: 600/600 generated inputs lawful, 12/12 sampled lessons
  identifiable, and 0/60 ambiguous held-out rotations.
* Large census: 300/300 lessons materialized, 1,500/1,500 production queries and
  1,500/1,500 rotations had no ambiguity against the declared rivals; 1,171
  unique input grids.
* Diversity gate: 270/300 unique inputs and outputs (90% each), 48 shapes.
* Override gate: 540/540 accepted draws, zero findings.

## Limits

These checks establish support against the three declared, canonical-fitting
ranking shortcuts over the sampled production domain.  They do not prove unique
induction against every possible hypothesis.  The deterministic five-role
schedule is intentional curriculum structure, not an IID sampler.  Generated
objects remain rectangular and use only colors 0 and 8, so the repair broadens
relative geometry and ranking evidence rather than the entire lawful input
space.
## Current reviewer considerations

Source SHA-256: `118d51fde17615f49b93040afce0bef735df4537c9074d23e694b2bd42d7f623`.

# Decisions for 5f5b990b28ab

## D1 — Preserve the Racket rule and pin it

**Observed problem.**  The baseline omitted `RULE_HASH`, but canonical examples,
Racket smoke tests, and a disconnected authority probe all agreed that the intended
operation is descending bounding-box-area ranking.

**Choice.**  Leave canonical Racket unchanged and add
`RULE_HASH = "d23e43212061"`.

**Alternatives considered.**  Restrict the Racket rule to nested frames, or rewrite
it to sort by perimeter.  Both would fit much of the baseline data but contradict
the selected authority probe and would narrow/change the task rather than repair its
teaching distribution.

**Failure mode controlled.**  Future rule drift now fails authority synchronization
instead of silently changing labels.

## D2 — Replace the baseline axis surface, rather than patch each dead axis

**Original rationale.**  The old names (`palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and textures such as `warm`/`cool`) suggested broad
variation, but their original design rationale was not documented.  Empirically,
four helpful textures were dead, two axes were singleton domains, and declared
values conflicted with per-band construction.

**Choice.**  Remove the non-falsifiable controls and expose one exact axis,
`scene_profile`, whose five values can be reconstructed from the grid.

**Alternatives considered.**  Keep grid height/width/count as independent exact
axes.  That would create many joint infeasibilities for nested depth-4 scenes and
would require a large incompatibility table without improving the semantic lesson.
Random texture labels were also rejected because an override must be observable in
the generated artifact.

**Probe.**  The override gate exercised 540 draws across every profile and band with
zero findings.  Task tests independently infer the profile from geometry.

## D3 — Use disconnected rectangular stress objects

**Choice.**  Add two stress profiles (three and four objects) built from box shapes
whose bbox-area order differs from scan order, cell count/perimeter, and width.
Horizontal reflection varies placement while preserving the disagreement.

**Why this shape family.**  It is the smallest change that isolates the ranking
feature while staying close to the canonical rectangular-object grammar.  The
objects remain easy to validate and the authoritative rule handles them directly.

**Alternatives considered.**  Filled rectangles, irregular blobs, touching objects,
or arbitrary colors.  Those would broaden more aggressively but confound object
extraction and ranking, and some are outside the documented canonical manifold.

**Known limit.**  A solver could still overfit to rectangular objects or the fixed
palette.  This repair targets the observed ranking ambiguity, not universal task
coverage.

## D4 — Make the lesson schedule deterministic and rotation-safe

**Choice.**  Cycle
`canonical_nested3 → area_stress3 → nested2 → area_stress4 → nested4`.
Every five consecutive pairs contain both stress roles.  With four demonstrations
and one query, holding out any one pair leaves at least one direct shortcut witness.

**Alternatives considered.**  Random profile sampling was rejected because even a
high stress probability permits rare all-nested lessons.  Per-lesson rejection
sampling was unnecessary once a five-role cycle gave a simple proof obligation.

**Tests.**  Task-local tests enumerate starts 0–11 and every query rotation; the
shared smoke checks 60 rotations; the larger census checks 1,500 rotations from 300
production lessons.

**Known limit.**  The downstream assembler must preserve consecutive schedule
positions.  If it independently shuffles or subsamples pairs before lesson assembly,
it must rerun identifiability on the assembled lesson.

## D5 — Declare only rivals that fit the canonical ambiguity being repaired

**Choice.**  Implement `scan_order`, `perimeter_order`, and `width_order` as
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with paired
witness predicates.

**Why these three.**  They fit the nested canonical examples and are simple,
plausible ranking hypotheses.  Each is directly refuted by both stress profiles.
Nesting depth is not a separate output function on disconnected scenes; it collapses
or becomes undefined, so scan/size/width rivals provide more reproducible executable
comparisons.

**Limit.**  Passing a finite declared-rival set is not proof against every possible
program.  This is stated in the generator notes and census limits.

## D6 — Strengthen `self_check` at the actual input boundary

**Choice.**  Validate nonempty rectangular grids, exact integer palette `{0,8}`, two
to four components, lawful rectangular perimeters (plus the canonical tiny solid
center), distinct bbox areas, and declared profile observability.  Return diagnostic
messages rather than throwing on malformed input.

**Alternatives considered.**  Accept any color-8 component the Racket rule can
process.  That is rule-lawful but too broad for a generator contract and would make
profile/override claims unverifiable.

**Failure probes.**  Foreign colors, booleans, ragged rows, erased frame edges,
merged components, and duplicate bbox areas all failed before the implementation and
are now rejected.

## D7 — Keep the oracle independent and call real Racket for parity

**Choice.**  Put an independent flood-fill/bbox oracle and rival implementations in
`workspace/reference_probe.py`, and have the task tests compare 5 canonical plus 20
generated grids to the actual staged Racket worker.

**Why.**  Reusing production helpers in tests would allow the same bug to appear in
both expected and actual results.  A Python-only mirror would not catch drift between
the mirror and selected authority.

**Limit.**  The helper is reviewer tooling, not production authority.  Racket remains
the label source.

## D8 — Retain red evidence and interrupted aggregate evidence

The baseline-facing test run (34 failed, 8 passed) is retained to show that the new
suite exercised missing behavior rather than merely documenting the final code.  The
first aggregate after run was interrupted by the foreground execution window; its
checkpoint is retained, and the exact-source `--resume` completion is reported
separately.  Neither is described as a semantic failure of final source.

## D9 — Stop after the stated domain is measured

No attempt was made to add arbitrary irregular shapes, variable source colors,
palette permutations, or more than four objects.  Those could be useful future
extensions, but they would increase rule/domain questions without evidence that they
are needed for this repair.  The selected result meets the rule pin, authority,
strict profile, override, semantic, rotation, diversity, and test gates while keeping
the change reviewable.
