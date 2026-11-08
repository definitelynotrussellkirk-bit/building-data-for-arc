## Current native extension — handoff `101306`

This handoff adds a separate native family in `workspace/parametric`; production
v3.0.0 and the exact canonical authority remain unchanged. The production
`generator.py` SHA-256 is
`943ae6682b0f4888022d61335ffcb098bf87b0f66c069e94c91bb1dd00d75255`,
the canonical program SHA-256 is
`a19a4990bac925a40190e810e985b52023a5854b4dcde3769b2251fa35432e8e`,
and the existing production rule hash remains `32695808b436`.

### Native semantics and sampling

`post=none` returns the exact canonical program. It finds monochromatic
4-connected blue components in the original input, processes them in row-major
first-cell discovery order, and fills each strict bounding-box interior with
its last original nonzero/nonblue seed in row-major order. Component discovery
and seed reads use the original grid; writes accumulate in order, including
writes over internal blue cells and earlier fills.

`post=largest_to_8` first performs that same fill, then finds monochromatic
4-connected components across the complete filled grid, excluding colors 0 and
1. It measures occupied cell count and recolors every maximum-area tie to 8;
freestanding colored components participate in this global selection.

The native grammar accepts rectangular 3–30 grids with a seeded interior for
every blue component bbox, including open blue objects, overlapping/nested
boxes, and freestanding colors. Both settings are total on this grammar.
Sampling supports 2–6 demonstrations (default 3) and 1–4 queries (default 4),
with matching inputs across settings and novel query inputs. Fixed-orientation
teaching cores vary by palette and translation; mosaics add D4 transforms,
variable intervals, and multiple seeds.

### Current evidence and retained history

Evidence is retained under `WORK/checks/486375757aca/` in this handoff:

| Check | Current result | Receipt |
| --- | --- | --- |
| Focused native and audit tests | 74 passed | `native-teaching-combined-tests-v1-command.json` |
| Sampler after the documentation correction | 96/96 passed | `sampler-v2.json` |
| Independent teaching audit | 72 rival cases; 124 distinct protected evaluations; 40 intended labels verified | `native-teaching-v2/audit.json` and `executions.json` |
| Qualification | 4 jobs; 64 protected evaluations | `qualification/qualification.json` |
| Causal replay | Two changes replayed, affecting 54 and 144 cells | `causal/witness.json` and `causal/replay.json` |
| Public preview verification | 16 public views verified | `preview-verify-command.json` |

The README-only correction changed the 30×30 query blue-cell count from 392 to
376; the corresponding demo count is 304. No algorithm changed. The current
sampler-v2 and teaching-v2 evidence binds the corrected documentation. The
initial audit-only Racket parenthesis failure and its diagnosis are retained
as failed historical evidence, not counted as a pass; the corrected audit has
current passing evidence.

Coverage is finite: these sampled seeds, settings, shapes, and declared rivals
do not establish universal identification or exhaustive grammar coverage.
Owner acceptance remains pending, and this handoff makes no training admission.

The inherited production scalar-coercion finding
`review-3ac21549f2aae7f7:v0001` remains `needs_triage`; strict native controls do
not repair production seed/sample-index validation. The inherited no-issue
audit `review-37a0be21af52db07:v0001` also retains its existing `needs_triage`
status. Neither audit disposition is changed by this extension. All historical
notes below are preserved verbatim.

---

# Working notes: 486375757aca

## 2026-09-28 review — assignment `review-353ef110c68adcd2`

### Authority and baseline diagnosis

The existing Racket authority was left unchanged.  Reading it literally showed
that it iterates 4-connected blue objects, takes each object's bounding box,
chooses the final non-{0,1} interior value in row-major order, and fills that
entire interior.  This is broader than the old written/generator assumption of
“one seed per separate frame.”  The canonical test makes the distinction
observable because two frames touch and form one component.

The v2.1.0 generator generated only two disjoint left/right frames with one
distinct seed each.  Its declared axes mostly did not affect output, its
`self_check` rejected two of four canonical inputs, it had no rule-hash pin or
semantic contract, and the override gate reported 12,742 findings.

### Selected design

Version 3.0.0 exposes one honest axis, `scene_profile`, with six fixed legal
geometries.  Profiles alternate between disconnected scenes and scenes with
joined frames.  Seed colors and legal interior positions remain randomized and
deterministic under `(seed, sample_index, version, task_id)`.

The fixed topology schedule is intentional rather than an attempt to maximize
layout entropy.  It guarantees that every cyclic three-demonstration window
contains a touching example and therefore falsifies all three declared rivals:

1. use the first seed in a blue component;
2. fill each detected frame independently;
3. preserve blue cells that happen to lie inside a merged component's box.

The generator now includes an independent Python mirror, canonical-accepting
validation, strict profile checks, observable override recovery, semantic
witnesses/rivals, and lesson-level identifiability checks.  The canonical
Racket program remains the authority; the mirror is a tested review aid.

### Rejected alternatives

- **Keep random disjoint placement and add rare overlaps.** Rejected because a
  rare semantic discriminator does not guarantee that a three-example lesson
  teaches the connected-component rule.
- **Expose many low-level axes (`grid_h`, `grid_w`, frame count, frame size,
  texture).** Rejected because many combinations are invalid or semantically
  redundant, and the previous implementation silently ignored most of them.
- **Generate arbitrary touching rectangles.** Rejected for this pass because
  proving complete-frame recovery, nonempty interiors, and consistent rival
  disagreement across all combinations would add complexity without improving
  the central curriculum guarantee.
- **Rewrite the Racket rule to match the prose.** Rejected because the existing
  executable source is synchronized across all authorities and solves all
  canonical pairs, including the touching-frame test.  Narrowing it would alter
  the task rather than repair the generator.

### Known limitations

- Geometry comes from six templates; diversity is primarily seed placement and
  color assignment.  The final diversity gate still reports 100% unique inputs
  across its sample, but only 52% unique outputs because the canonical fill
  deliberately erases much input variation.
- Difficulty bands rotate the same curriculum rather than claim an externally
  calibrated difficulty scale.
- `observe_overrides` identifies generated profiles by their unique dimensions.
  It is exact for generated instances but intentionally does not claim to
  reconstruct arbitrary canonical layouts from geometry alone.
- The self-check mutation probe rejected 54/55 destructive mutations.  The one
  surviving `absent_color_cell` mutation did not violate the actual seeded-frame
  grammar; broadening rejection to catch it would risk rejecting valid inputs.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `943ae6682b0f4888022d61335ffcb098bf87b0f66c069e94c91bb1dd00d75255`.

# Input-distribution decisions for `486375757aca`

## Design objective

Teach the exact selected Racket behavior, not merely produce grids that the
program can execute.  A three-example lesson must expose connected-component,
bounding-box, last-seed, and internal-overwrite semantics strongly enough to
falsify the best simple rival rules.

## Decisions

### D1 — Treat the executable authority as component-based

- **Original rationale:** Unknown.  The old docstring and summary described
  independent frames, but the preserved program iterates blue objects.
- **Choice:** Define the task by 4-connected blue components and their bounding
  boxes.  Touching frames are one object.
- **Alternatives considered:** Rewrite the Racket rule to match the prose; keep
  generating only disjoint frames.
- **Probe:** The canonical test has two touching frames.  The program fills their
  combined box with the final row-major seed and overwrites internal blue cells.
- **Failure mode avoided:** A generator that validates only the easier prose
  trains a model to fail the canonical query.
- **Limitation:** The written canonical description remains narrower than the
  executable behavior; this review corrects task-local documentation only.

### D2 — Leave the Racket source unchanged and pin its hash

- **Original rationale:** The source was already selected and retained in three
  authority locations.
- **Choice:** Add `RULE_HASH = "32695808b436"`; do not edit canonical or archival
  Racket.
- **Probe:** Authority-sync reports exact synchronization and execution parity on
  all four canonical pairs.
- **Failure mode avoided:** Unreviewed semantic drift or a generator-specific
  fork of the task.

### D3 — Replace low-level axes with one observable `scene_profile` axis

- **Original rationale:** The old eight/nine-axis declaration appears to have
  been inherited from a generic template; most names were not used by code.
- **Choice:** Expose only six named, directly observable scene profiles.
- **Alternatives considered:** Repair each old axis; mark dead axes diagnostic;
  allow arbitrary grid/frame combinations.
- **Probe:** The override gate exercises all six values across all three bands;
  630/630 draws pass and unknown keys are rejected.
- **Failure mode avoided:** Typoed overrides, silent no-ops, invalid axis
  combinations, and metadata that claims variation the generator does not emit.
- **Limitation:** Users cannot independently request arbitrary dimensions or
  frame counts; they select a validated semantic profile instead.

### D4 — Use six fixed legal topologies with unique dimensions

- **Original rationale:** The old generator used random left/right placement,
  likely for implementation convenience rather than semantic coverage.
- **Choice:** Use six templates spanning 2–3 frames, edge anchoring, a narrow
  canonical-like frame, disconnected layouts, a touching pair, an
  isolated-plus-touching layout, and a touching chain.
- **Alternatives considered:** Rejection-sampled arbitrary rectangles; a larger
  template bank; only canonical layouts.
- **Probe:** Complete-frame recovery and `self_check` accept every profile in all
  bands; the semantic gate samples every profile; the canonical profile floor
  accepts 4/4 canonical inputs and 60/60 generated envelope cases.
- **Failure mode avoided:** Accidental open frames, empty interiors, undetected
  frame merges, or a profile observer that cannot recover the requested axis.
- **Limitation:** Topological entropy is bounded by six templates.

### D5 — Alternate touching and disconnected profiles

- **Original rationale:** No prior curriculum schedule existed; all normal cases
  were disconnected.
- **Choice:** Order profiles disjoint/touching/disjoint/touching/disjoint/touching
  and schedule cyclically, with band-specific phase offsets.
- **Alternatives considered:** Uniform random profile selection; rare touching
  cases; one fixed touching demonstration.
- **Probe:** Focused tests enumerate every three-example window; all three
  declared rivals are falsified.  The semantic gate confirms 12/12 sampled
  lessons identifiable.
- **Failure mode avoided:** A learner seeing three easy disjoint examples and
  adopting “fill each frame independently.”
- **Limitation:** `difficulty` changes curriculum phase, not measured complexity.

### D6 — Randomize seed positions and sample distinct colors

- **Original rationale:** The old generator used one random, distinct seed per
  frame.
- **Choice:** Keep one seed per complete frame, sample distinct colors 2–9, and
  place each seed anywhere in its nonempty interior.
- **Alternatives considered:** Multiple seeds per individual frame; repeated
  colors; fixed seed positions.
- **Probe:** Touching profiles necessarily contain multiple distinct seeds in
  one blue component, so first-vs-last seed behavior is visible.  Rule smoke
  sees 81 distinct outputs and 120/120 mirror parity.
- **Failure mode avoided:** Same-color seeds hiding the row-major selection rule,
  or fixed positions permitting a spatial shortcut.
- **Limitation:** Multiple seeds arise through merged frames rather than within a
  single rectangular frame.

### D7 — Permit internal blue borders to be overwritten

- **Original rationale:** The old prose said borders are preserved, which is true
  only for disconnected frames.
- **Choice:** Validate and generate touching cases in which a frame border lies
  inside the merged component's bounding box; the authoritative fill overwrites
  it.
- **Alternatives considered:** Touch only at a corner (not 4-connected); touch
  without putting blue cells in the combined interior.
- **Probe:** `internal_blue_overwritten` fires on 305/600 semantic-gate samples;
  the `preserve_internal_blue` rival is contradicted in all 60 claim checks.
- **Failure mode avoided:** Teaching “blue is always immutable.”

### D8 — Recover complete frames separately from blue components

- **Original rationale:** The old validator assumed each blue component was one
  rectangular frame, which is false for touching frames.
- **Choice:** Enumerate complete rectangular blue borders for grammar validation,
  while independently computing 4-connected components for rule behavior.
- **Alternatives considered:** Validate only components; store hidden template
  metadata; accept any blue shape.
- **Probe:** The validator accepts the canonical touching test and still rejects
  stray blue cells, seeds outside frames, empty interiors, ragged grids, and
  malformed values.
- **Failure mode avoided:** Rejecting lawful touching scenes or accepting
  arbitrary component shapes not supported by the frame grammar.
- **Limitation:** Exhaustive rectangle enumeration is quadratic in candidate row
  and column pairs, but ARC bounds and measured runtime keep it inexpensive.

### D9 — Add an independent mirror and explicit rivals

- **Original rationale:** The old generator had no semantic hooks.
- **Choice:** Implement a readable Python transcription plus three rivals and
  three witnesses, all exercised by focused tests and the inherited semantic
  gate.
- **Alternatives considered:** Depend only on Racket smoke; compare output hashes
  without named hypotheses.
- **Probe:** Mirror parity is 120/120 in rule smoke and exact on all four canonical
  pairs.  The semantic gate verifies 3/3 witness and rival claims.
- **Failure mode avoided:** A validator that checks syntactic validity but cannot
  state what misconception a generated example rules out.
- **Limitation:** The mirror is review tooling, not authority; future Racket edits
  must update the rule hash and parity tests.

### D10 — Remove ordinary degenerate textures

- **Original rationale:** The old generator exposed `no_seed`, `frames_overlap`,
  and `single_frame` through the same valid texture domain as normal examples.
- **Choice:** Declare no helpful or degenerate texture axis for this task.
- **Alternatives considered:** Retain negative fixtures behind a separate
  diagnostic-only API.
- **Probe:** Strict defect lint reports zero findings; override contract reports
  no invalid normal cases.
- **Failure mode avoided:** Training on inputs for which the authority crashes or
  for which the stated task is undefined.
- **Limitation:** There is no public negative-fixture generator; malformed cases
  are instead covered by focused validator tests and mutation probes.

### D11 — Accept canonical grammar, not only generated templates

- **Original rationale:** The old `self_check` required exactly two independent
  4x4-or-larger frame components and therefore rejected lawful canonical cases.
- **Choice:** `self_check` recognizes complete seeded frames and component-level
  authority preconditions without requiring generated dimensions.  The stricter
  hook adds the canonical/generated shape envelope for semantic-gate sampling.
- **Probe:** 4/4 canonical inputs accepted; 54/55 destructive mutations rejected.
- **Failure mode avoided:** A generator that passes on its own narrow outputs but
  contradicts the source task.
- **Limitation:** One mutation class can remain lawful after deleting a color;
  rejecting every mutation is not itself the semantic goal.

### D12 — Preserve deterministic source binding and fresh return values

- **Original rationale:** Required by the repository generator contract.
- **Choice:** All random choices derive from `gen_ctx`; repeated calls return
  equal but independently allocated grids.
- **Probe:** Focused determinism/freshness tests cover all bands and schedule
  recovery.
- **Failure mode avoided:** Global RNG leakage, stateful generation, or aliased
  mutable outputs.
