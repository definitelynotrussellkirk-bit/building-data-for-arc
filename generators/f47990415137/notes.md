# Working notes: f47990415137, review-a7f6d58e1698f2aa

## Current parametric extension — review-4297489dafda6d75

The canonical generator and exact canonical Racket text remain unchanged.
`workspace/parametric/` now provides native `reference=axes|largest` settings.
The alternate rule selects the unique largest monochrome component by foreground
cell count, then uses its bbox aspect as the reference for every object's
recoloring. Exact cross multiplication preserves the original bbox reasoning.
This is an input-derived comparison dependency, not an updated-grid simulation.

The adapter supports 2–6 demos and 1–4 independently counted queries, using three
demos/four queries normally. Both settings share identical input draws. Six-role
teaching scenes contain scaled ratio equality, repeated colors, sparse objects,
both comparison sides, and a nonsquare bbox maximum distinct from the cell-count
maximum. Four-query episodes include substantive 8×8 and 30×30 boundaries.
The new family alone extends size support to 30; production stays at 8–20.

Two real teaching holes were retained and repaired: seed 22 allowed a first-raster
reference rule to fit two demos but disagree on two queries; seed 3 allowed a
bbox-area reference rule to fit the axes demos but fail on the 30×30 query.
Protected before cases are `checks/f47990415137/first-raster-before.json` and
`checks/f47990415137/bbox-selector-before.json`. The constructive repair fixes
the earliest object's vertical position and gives the sparse mild-aspect object
the largest nonsquare box. Reference count lower bounds prevent distractor ties.

Current evidence: 60 new tests passed; eight episodes/58 pairs and 381 protected
Racket evaluations passed the eight-rival audit, including the first two demos
alone. The 30×30 boundary contains nine objects and 197 foreground cells spanning
all edges. A separate Python sweep passed 4,761 scenes and 768 generated episodes.
See `workspace/parametric/evidence/current/audit-final.json` and the source-bound
inventory. Native qualification passed both settings on seeds 0 and 17 at 3/4
counts; the causal witness was protected-Racket replayed against that exact source.
The counterfactual changes the selected reference from a 4×2 cell-count maximum
to a 4×3 bbox-area maximum, changing labels on other unchanged objects.

Public example export now has a one-command Racket-verified builder and a
single-query turn projection. Hidden settings, programs, labels and future
queries remain private; filenames hash visible bytes only. The slot grammar
excludes touching objects and does not distinguish 4- from 8-connectivity.
The tests cover finite rival families, not universal uniqueness or learning gain.
Reviewer status is ready; exact-source owner acceptance and training admission
are not granted by this return. The next owner step is qualification and
acceptance after integrating these exact files, as the packet contract requires.

## Earlier canonical review

## Authority and initial defect

The rule labels monochrome 4-components by bbox height versus width, retaining
zeros inside irregular objects' bounding boxes. All four canonical pairs have
uniquely colored filled rectangles. Both `group_by_color` and
`fill_bounding_boxes` fit all four canonical outputs, so those pairs alone do
not identify the full rule against these rivals.

The selected v2.1.0 baseline had no rule pin, silently ignored palette/density/
position/texture controls, clamped nominal dimensions by difficulty, used a
small fixed shape library, and could silently reduce the object count in a
fallback. Its validator prohibited same-color disconnected objects. The before
battery fails lint, defect_lint, and override; the profile floor and semantic
checks are advisory, not passes. No prior return was used as evidence or a lead;
the task's imported associated-notes file was empty.

## v3 design and migration

Keep labels exclusively in unchanged Racket. Python generates only inputs;
Python mirrors/rivals are tests and authoring evidence, not training authority.

Retain exactly four controls: grid_h/grid_w in 8..20, n_blobs in 3..6, and
n_distinct_colors (foreground only) in 1..6. Legal requests are exact in every
band. More colors than objects raises a structured incompatibility; requesting
only a large palette automatically selects enough objects. Unknown/removed
controls raise ValueError. The old palette_size, palette_kind, density,
position_bias, and texture aliases are deliberately removed, not reinterpreted.
The old 7-cell dimension is no longer supported. Downstream configurations
using these old controls need an explicit migration; VERSION is bumped to 3.

Defaults repeat a color on tall and wide objects, guaranteeing a witness against
color grouping. A nonrectangular square-bbox component refutes box filling.
All-distinct palettes remain valid exact controls and canonical inputs remain
accepted; such overrides are not promised to refute color grouping.

Connected shapes begin as a bbox-spanning L and grow by cardinal adjacency, with
optional filled rectangles and random flips. Bboxes span at most 6x6. Random
placement comes first; a randomized slot partition handles crowded grids without
dropping any requested object. A test forcibly enters this fallback. All three
aspect classes appear in every generated input. The first raster component's
aspect varies across all three classes in every 128-draw test band.

A 60% core branch strongly weights dimensions 10x12 and (when feasible) three
foreground colors, with four objects favored. A broad branch supports every
8..20 dimension. All bands retain the core; hard favors six objects only in the
broad branch. These are task-specific sampling weights, not universal ARC
principles or a calibrated difficulty scale. The final profile-floor sample
hits exact canonical size/palette profiles in 10/20 easy, 8/20 medium, 11/20 hard
draws. This is distribution support, not exact-grid copying or a proof of
canonical shape-distribution fidelity.

## Evidence and limits

Final generator SHA256:
`d008e332f8f238dbf8d6b022acbfdf1fa73005a9d10f7637ddb798086c8458b7`.
Full before/after receipts, red tests, production lesson census and independent
oracle comparisons are in the returned `checks/` evidence, indexed by RESULTS.json.
The task suite has 67 tests, including the reusable role probe's fail-closed tests.

300 production lessons (100/band; three demonstrations plus one query) contain
1,200 unique inputs. None is ambiguous against the two declared rivals in its
original order or across all 1,200 possible single-query role windows. The
independent BFS oracle agrees with the retained Racket labels on all 1,200 pairs.
These overlapping windows are not 1,200 additional generated inputs.

Self-review: 8-separated objects make 4-connectivity and 8-connectivity equivalent
on this sampler, and default irregular square objects mean it cannot establish
coverage of rectangle-only lessons, touching shapes, or every possible connected
shape. Palette/position randomization and per-input counterexamples remove the
two measured shortcuts, but they do not prove universal identifiability or a
Qwen3.5-9B learning gain; the rectangular validator domain is intentionally
broader than the default sampling distribution.
## Current reviewer considerations

Source SHA-256: `d008e332f8f238dbf8d6b022acbfdf1fa73005a9d10f7637ddb798086c8458b7`.

# Decisions — f47990415137 / review-a7f6d58e1698f2aa

## M1 — Give controls a truthful, pixel-observable meaning

**Observed:** the baseline ignored palette_kind, palette_size,
n_distinct_colors, density, position_bias and texture choices, and nominal
dimensions could be clamped by difficulty. Advertising those controls creates
false coverage claims. The baseline's original reasons are unknown; its notes
contain no justification.

**Chosen:** exactly four axes: 8..20 height and width, 3..6 components, and 1..6
foreground colors. `observe_overrides` recovers all four. Accept legal requests
in all difficulty bands. If colors exceed objects, raise a structured
incompatibility naming both axes. When only a large palette is requested, pick
enough objects. Reject invalid types, bools, unknown axes and removed legacy
controls. Canonical Racket is unchanged; pin its normalized RULE_HASH.

**Rejected:** implement many overlapping palette/texture aliases merely to keep
the old signature. That adds poorly specified combinations without teaching the
rule. Silently accepting removed controls would recreate the bug. This is a
v3 migration, not a backwards-compatible promise: old configurations need their
ignored keys removed or deliberately translated; grid dimension 7 is no longer
supported. The minimum 8 permits a simple constructive exact-count fallback at
six objects without losing any of the four canonical size/palette profiles.

**Probe:** initial red tests; final 44,280-attempt override contract, including
540 declared incompatibilities and zero errors/warnings. Counts and seed recipe
are in `checks/SAMPLING.md`. Tests cover single-axis palette requests, legal
joint requests on an 8x8 canvas in all bands, invalid types and typo rejection.

## M2 — Identify components rather than color identities

**Observed:** all canonical pairs and old defaults assign unique input colors
to each blob. A rule merging disconnected components by color therefore fits
the canonical evidence. Requiring different colors in self_check protects the
shortcut rather than the intended semantics.

**Chosen:** default colors repeat across at least one tall and one wide object.
Because the two objects require different output colors, no global rule that
maps each input color to one output color can satisfy that input. Other colors
and positions are random. All three bbox aspect classes appear in every input.
Explicit all-distinct palettes remain legal to preserve a useful controlled
subdomain and canonical acceptance.

**Rejected:** duplicate colors arbitrarily without requiring different aspect
classes. Same-color objects with the same output class need not distinguish the
rival. Also rejected: make repetitions occasional but rely only on aggregate
frequency; short lessons could then omit the sole witness.

**Probe:** actual declared CANONICAL_SHORTCUTS fit 4/4 canonical pairs; per-input
witness and rival checks; 300 production lessons plus all four query roles.
Explicit all-distinct overrides are not advertised as retaining this witness.

## M2 — Preserve zero cells inside bounding boxes

**Observed:** canonical objects are filled rectangles, so filling each bbox is
another canonical-fitting wrong rule. Enlarging rectangles alone does not
remove it.

**Chosen:** one square-bbox object must be nonrectangular. Shapes use a connected
L spanning their bbox, randomized connected growth, optional rectangles for
other objects, and flips. This preserves connectivity and aspect constructively.
Bboxes may reach 6x6, rather than the baseline's tiny fixed-template menu.

**Rejected:** force all objects to be irregular, which would unnecessarily
eliminate rectangular components. Also rejected for this patch: a rectangle-only
default subdistribution that requires a more fragile lesson-level witness
schedule to distinguish box filling. Such a future schedule could be useful,
but would need a complete assembly/rotation audit rather than a frequency claim.

**Limitation:** every default input has an irregular square-bbox object; this
is a teachability guarantee and a distribution restriction. L-growth plus flips
does not span every connected polyomino. No hollow/touching-object or topology
coverage claim is made.

## M3 — Make crowded generation terminate without changing the request

**Observed:** a retry fallback could quietly shorten the object list. Rejection
alone would also make supported extreme combinations unreliable.

**Chosen:** bounded random placement first, then a randomized 2x2 or 2x3/3x2
partition with empty separator rows/columns. Each slot is at least two cells
wide/high, enough for tall, wide and irregular square-bbox witnesses. Its shapes
and placement offsets remain randomized. The fallback produces exactly n_blobs
and every chosen foreground color, never a shorter task.

**Rejected:** unrestricted retry loops, silent object dropping, and one fixed
fallback canvas. A monkeypatch forces fallback in tests for every object count
3..6 at 8x8. Every supported input still has mutually 8-separated components.

**Limitation:** fallback slot structure can leave a layout signature. It does
not induce a fixed raster aspect ordering in the tested defaults (each band
shows all three first-component classes), but this is not a proof that all
placement shortcuts are impossible. Touching and diagonal-only distinctions
are deliberately outside this sampler.

## Keep canonical-scale support without equating “strict” with copying

**Observed:** before exact-profile support was 1/60 and absent in two bands;
larger/harder sampling alone had drifted away from canonical-size/palette cases.

**Chosen:** a 60% core branch strongly favors 10x12 and three foreground colors,
with four objects favored, plus a broad branch over every 8..20 dimension. All
bands retain the core; hard favors six objects in its broad branch. Shape and
layout draws stay stochastic. `strict_canonical_like` means valid task-domain
inputs, including canonical rectangles and repeated-color irregular witnesses;
it does not pretend that all defaults reproduce the canonical shape distribution.

**Rejected:** seed-specific patches to pass the profile gate, copied canonical
grids, and universal size/color restrictions imported from another task. The
mixture is explicit task-specific sampling policy. All four canonical input
profiles are possible, but the measured 29/60 exact hits do not establish equal
support for each individual canonical profile. Difficulty is not calibrated to
measured model performance.

## F1 — Preserve distinctions after a consumer changes example roles

**Observed:** ba090ac77d54's original four-demo lessons each contain their needed
metric witnesses. Putting one such demonstration in the query position can
remove the only example separating Manhattan from a conditional Euclidean rule:
108/360 role windows fail, while 0/72 original lessons fail.

**Chosen:** add a source-bound reusable authoring tool under the selected task's
workspace. Reuse actual retained Racket labels and actual LESSON_COMPETITORS;
compute per-pair rival agreements once, then score each query role. Reject missing
rivals, empty/incomplete evidence and source mismatch rather than reporting a
vacuous pass. Three fail-closed tests were first observed failing, then repaired.
The selected task is a positive control (0/1,200 failing roles).

**Rejected:** alter an audit target or shared exporter in this assignment, or
reject ordered lessons merely because an unused role permutation would fail.
Shared integration belongs at the actual augmentation boundary; see the one
prioritized F1 recommendation and QUESTION_ANSWER.md. No measured model gain is
claimed. Root and selected suites were both explicitly run.

## Solve integrity

Complete the unrelated blind episode before authoring inspection; later solve
only the visible post-repair challenge while keeping rule/generator/reference
answers closed. The second episode is exposed, not blind. Both first attempted
programs passed all visible examples. There was no natural failed solve revision
to retain; do not invent one or relabel the intentional rival probes as model
mistakes. Frozen notes describe a work log, not captured token-level reasoning.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-2f4f897fe5f87c8d:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d008e332f8f238dbf8d6b022acbfdf1fa73005a9d10f7637ddb798086c8458b7`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/f47990415137/generator.py, unchanged SHA256 d008e332f8f238dbf8d6b022acbfdf1fa73005a9d10f7637ddb798086c8458b7. Bounded clean:67 tests,600 strict draws,12 ordered lessons/48 diagnostic rotations identifiable;5760 deterministic draws,2510 unique, no observed failures. Exact report/source retained in generators/f47990415137/evidence/bounded-audit-2f4f897fe5f87c8d/manifest.json. Quoted basenames mean these exact target-local paths: `checks/audit/f47990415137-combined-command.exit` `checks/audit/f47990415137-combined-command.log` `checks/audit/f47990415137-combined/RUNTIME_MANIFEST.json` `checks/audit/f47990415137-combined/checks/f47990415137_audit_battery_summary.json` `checks/audit/f47990415137-combined/checks/f47990415137_audit_commands.jsonl` `checks/audit/f47990415137-combined/checks/f47990415137_audit_semantic_gate.json` `checks/audit/f47990415137-combined/checks/f47990415137_audit_semantic_gate.log` `checks/audit/f47990415137-combined/checks/f47990415137_audit_semantic_gate.ok` `checks/audit/f47990415137-combined/checks/f47990415137_audit_semantic_gate.receipt` `checks/audit/f47990415137-combined/checks/f47990415137_audit_summary.json` `checks/audit/f47990415137-combined/checks/task_tests.xml` `checks/audit/f47990415137-combined/progress.log` `checks/audit/f47990415137-combined/result.json` `checks/audit/static-generation-fuzz.json`

### Assessment or prior finding

## f47990415137

**Conclusion: No issue found.** Source SHA-256: `d008e332f8f238dbf8d6b022acbfdf1fa73005a9d10f7637ddb798086c8458b7`.

I checked the portable task suite, strict-canonical acceptance, declared semantic witnesses and rivals, ordered lesson assembly, every diagnostic query rotation in the sampled lessons, deterministic generation, input validation, and generation crashes.

Measured results:

- 67/67 portable tests passed (`checks/audit/f47990415137-combined/result.json`).
- 600/600 generated draws passed `strict_canonical_like`, with zero crashes or hook errors.
- 12/12 three-demonstration/one-query lessons were identifiable against the declared rivals.
- 48/48 diagnostic held-out query rotations were identifiable, with zero hook warnings or scoring errors.
- An additional deterministic sweep covered 5,760 draws (120 seeds × 16 sample indices × 3 bands), 2,510 unique normalized inputs, with no exception, nondeterminism, or `self_check` failure (`checks/audit/static-generation-fuzz.json`).

The canonical examples admit the declared `group_by_color` and `fill_bounding_boxes` shortcuts, but generated witnesses refute both in all checked lessons. This is finite-domain evidence, not a proof against undeclared programs; I found no concrete defect or unsupported shortcut in the tested generator domain.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
