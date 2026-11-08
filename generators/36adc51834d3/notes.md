# Working notes: 36adc51834d3

## Review 2026-10-03 — assignment review-68e586aabe594108

Baseline generator SHA-256: `fd33e094b9b8304102fa6bb9320ba54337f729573fcc6751fddda59b0aeb113b`.

The baseline battery produced 8 green stages, one semantic advisory, and three failures. The actionable defects were:

- no pinned `RULE_HASH`;
- seven advertised controls that were dead, singleton, aliased, or narrowed by difficulty instead of being exact global overrides;
- ordinary `texture` values overlapping negative/degenerate fixtures;
- unknown override keys silently accepted;
- no executable semantic contract or lesson schedule;
- only 42/75 destructive mutations rejected;
- a narrow shape/output distribution (63% unique outputs in the 300-pair probe).

## Selected design

Version 2.0 replaces metadata drift with five observable controls:

- `grid_h`: 6..14;
- `grid_w`: 6..14;
- `blob_size`: 3..10;
- `cmd`: 1..4;
- `color_relation`: `same|different`.

The sampler is constructive rather than rejection-driven. It enumerates 8-connected shapes in a local 4×4 box, retains only shapes with at least a 2×2 bounding box and four distinct quarter-turn views, then chooses a legal placement. Canonical-size priors preserve task resemblance without narrowing any override domain. `cmd = 1 + sample_index % 4` makes every four-example lesson cover all transformations; the relation schedule alternates so each command appears with both same-color and different-color objects across two cycles.

The semantic contract includes canonical-envelope validation, command witnesses, executable rivals, lesson competitors, a four-command identifiability check, schedule profiles, and destructive mutation fixtures. `CANONICAL_SHORTCUTS` is intentionally empty: none of the tested wrong rules reproduces every public pair; `ignore_command`, `always_cw`, and `marker_only` are lesson competitors instead.

## Late extended-lesson finding and repair

The 12-lesson battery smoke passed, but a required 300-lesson run found one failure at easy lesson 41 (`seed=222845685425138`, `sample_index=451`). A valid object surrounded the command corner so its bounding box contained `(0,0)` without occupying it. `_analyze` excluded the command from the object-cell set but cropped the original grid, leaking the command token into the semantic crop. A test was added first and failed; version 2.0.1 now clears `(0,0)` in a copy before cropping, matching the Racket authority. The focused suite increased to 24 tests.

## Remaining limits

- This is a compact task-specific curriculum, not a claim that these five axes span all perceptually meaningful ARC variation.
- Connectivity follows the canonical data: one 8-connected perceptual object. Two public objects are not 4-connected.
- Difficulty is sampling weight only; it never changes the declared legal override domain.
- The semantic rivals cover the principal command/rotation shortcuts, not every conceivable solver.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `9d9f8b2de28ef53ed00e906725ad362a5a560f9c43c4fdb8a2b8073bafb4a40a`.

# Decisions for 36adc51834d3

Final generator: version `2.0.1`, SHA-256 `9d9f8b2de28ef53ed00e906725ad362a5a560f9c43c4fdb8a2b8073bafb4a40a`.

## D1 — Replace metadata aliases with five exact pixel controls

**Choice.** Keep only `grid_h`, `grid_w`, `blob_size`, `cmd`, and `color_relation`.

**Why.** Each can be recovered from the returned grid. The baseline advertised panel counts, motif/palette aliases, singleton layout/density values, and degenerate textures that either did nothing or bypassed the task grammar. Exact axes are now validated for unknown keys and types, and every declared value is constructive in every band.

**Rejected alternative.** Preserve old names for compatibility. That would retain misleading controls and make typo acceptance look like successful coverage. No external task-specific API in the packet required them.

**Probe/failure mode.** The override gate exercises 424 cases over three bands; focused tests pin low/high values and unknown/type rejection.

## D2 — Use one 8-connected monochrome object

**Choice.** Validate 8-connectivity, not 4-connectivity.

**Why.** Two canonical objects join only diagonally. An initial 4-connected interpretation rejected valid public data; the first green attempt exposed this and was corrected before acceptance.

**Rejected alternative.** Split diagonal components or restrict the sampler to 4-connected polyominoes. Both would narrow the task away from canonical evidence.

**Limit.** “One object” here is perceptual 8-connectivity, a task-local choice rather than a corpus-wide rule.

## D3 — Construct transform-revealing shapes from a cached catalog

**Choice.** Enumerate 3..10-cell subsets of a local 4×4 box, keep 8-connected shapes with at least a 2×2 box and four distinct quarter-turn views, then sample legal placements.

**Why.** This removes rejection loops, makes every size constructive, and prevents square/rotationally symmetric shapes from hiding the command mapping.

**Rejected alternatives.** Random walks can duplicate cells, produce hard-to-control sizes, and require rejection. Handwritten shape lists would be brittle and sparse. Arbitrary disconnected pixels would violate the canonical visual object.

**Limit.** Local object boxes are at most 4×4; the task does not need larger motifs to teach the rule, but this is not universal shape coverage.

## D4 — Schedule all four commands in every lesson

**Choice.** `cmd = 1 + sample_index % 4`; `EXAMPLES_NEEDED = 4`.

**Why.** Four consecutive demos expose identity, clockwise, 180°, and counterclockwise transformations. Random commands can omit a mapping and leave `ignore_command` or one fixed rotation alive.

**Rejected alternative.** IID command sampling. Even with good marginal frequencies it cannot guarantee a complete lesson.

**Probe.** The lesson hook requires all commands and refutes `ignore_command`, `always_cw`, and `marker_only`. Schedule profiles make cyclic coverage auditable.

## D5 — Vary whether object color equals command color

**Choice.** `color_relation` is an exact `same|different` axis, scheduled across two four-example cycles.

**Why.** Without both relations, a model may mistake command identity for object color or treat the corner token as a palette cue rather than an operation selector.

**Rejected alternative.** Make object color always different for visual separation. Easier perception would create a stable shortcut absent from some canonical examples.

## D6 — Use canonical priors without narrowing override domains

**Choice.** Difficulty changes sampling weights, not legality. Canonical dimensions 8..10 × 9..12 and sizes 5..6 receive a 75%/65%/55% core prior in easy/medium/hard, while full ranges remain available everywhere.

**Why.** The baseline narrowed per-band `draw_int` bounds, causing declared global overrides to fail. A weighted full-domain choice preserves exact controls and still gives every band canonical-profile support.

**Rejected alternative.** Fixed band ranges. They are simple but violate the advertised override contract and can make hard/easy separate domains rather than curricula.

## D7 — Permit corner-surrounding objects, but clear the command before crop

**Choice.** Object cells may be placed in row 0 or column 0 provided they do not occupy the 2×2 command zone. `_analyze` now clears `(0,0)` in an object-only copy before forming the bounding-box crop.

**Why.** The Racket rule removes the command before cropping. The 300-lesson probe found a rare legal case whose bounding box enclosed the command; the old helper leaked command color into one semantic check.

**Rejected alternative.** Forbid every placement whose bounding box contains `(0,0)`. That would hide the bug by narrowing the distribution and remove useful positional variation. Fixing the crop matches authority at the source.

**Evidence.** Exact replay in `checks/lesson-41-reproducer.json`; RED/GREEN tests in `checks/lesson-41-tdd-red.log` and `checks/lesson-41-tdd-green.log`.

## D8 — Separate canonical shortcuts from lesson competitors

**Choice.** `CANONICAL_SHORTCUTS` is empty. `ignore_command`, `always_cw`, and `marker_only` live under `LESSON_COMPETITORS`; two are also executable semantic rivals tied to command witnesses.

**Why.** None reproduces all five public pairs. Calling one a canonical shortcut would falsely claim the public data cannot refute it.

**Probe.** A focused regression iterates every declared canonical shortcut over every canonical pair.

## D9 — Keep Racket authority unchanged

**Choice.** No canonical/base solution or Racket source was edited.

**Why.** Rule smoke and authority sync passed before and after. All failures were in Python sampling, validation, or semantic metadata.

## D10 — Preserve failures rather than polishing them away

The baseline battery, TDD RED logs, two failed extended-semantic invocations (missing Racket PATH), the genuine 299/300 semantic failure, and stale pre-fix green battery remain under `checks/`. They distinguish harness mistakes from the actual rare defect and bind every claim to the source hash used.
