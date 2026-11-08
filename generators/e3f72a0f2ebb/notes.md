# Current notes: e3f72a0f2ebb

## Rule and current implementation

Version 4.0.0, generator SHA-256 `e8d40d9158ab2f44ad2a3964d4cebf835bfea909effebcd8c6ce1573ba2a970f`.
The selected Racket authority is unchanged; `RULE_HASH = "8d3a7f6a327b"`.
For each same-color, orthogonally connected nonzero component, draw the border
of its tight bounding box at its original location on an initially zero grid.
Different disconnected components may have the same color. A singleton, line,
thin rectangle or complete rectangular frame may already equal its answer.

Production emits 2–4 objects in disjoint rectangular regions separated by a
blank row or column. The validator admits the broader 1–4-object domain,
including every labeled canonical input, while rejecting malformed grids,
empty scenes and overlapping component bounding boxes. Color 0 is background;
colors 1–9 are interchangeable foreground values.

## Reversed choices and evidence

The original rationale for undocumented restrictions is unknown. This review
used prior finding `review-71b0731efc93daf1:v0001` as a lead, then reproduced the
defects against the selected baseline
`fed11c7fd24ea1f929b98322752a5e1a4345dcfcf8406285a5db5d93eb4bb85b`.

- **R1:** Replaced rejection of already-framed components with lawful fixed-point
  acceptance. The old check rejected canonical training pair 1. All four labeled
  canonical inputs now pass. Single-object endpoint evidence also uses actual
  Racket labels; acceptance is not a generic linter exemption.
- **R2:** Replaced input-pixel clearance with reserved whole output rectangles.
  The old medium seed 503/index 26 scene has two frames meeting at (4,6), despite
  passing its validator. The saved counterexample and tests cover this failure.
- **R3:** Replaced silently ignored controls with four exact integer axes:
  height 7–18, width 8–18, object count 2–4, distinct foreground colors 1–4.
  Unknown/retired keys and incompatible explicit color/object counts raise
  errors. The color count alone adjusts the sampled object minimum.
- **R4:** Replaced always-distinct object colors with repeated colors in phases
  1 and 3 of a four-phase schedule. The per-color bounding-box rival fits all
  four canonical pairs but fails on the retained easy seed 0/index 1 witness.
  Odd phases also contain an unchanged component; every scene contains a
  component requiring both added border pixels and erased interior pixels.

`EXAMPLES_NEEDED = 4` and `LESSON_SCHEDULE_PERIOD = 4`. Even phases favor
canonical size/palette-cardinality profiles in every difficulty band. Shapes,
palette, positions, cuts and full dimension ranges still vary. Controls are
observable from the grid, rather than inferred from generation requests.

## Verification and remaining decision

The review return for assignment `review-165607be772304c5` contains the exact
commands and receipts. The same 65-test suite gives 55 failures/10 passes on the
baseline and 65 passes on the repair. A direct finite scan checked 3,072 default
draws and all 1,188 compatible joint axis tuples at seed 0, four phases and
three bands (14,256 draws); 4,752 incompatible requests were rejected.
Forty-six selected unique witnesses received actual public Racket labels.

The strict after battery passed 11/12 stages. The remaining `defect_lint`
stage reports `selfcheck-power` and `selfcheck-minimal-impostor`: generic tests
expect some singletons, lines and solid rectangles to be rejected, although
these are lawful for this rule. Twelve explicit endpoint labels and six
negative validator controls are retained in the return. This is evidence for
maintainer adjudication, not a cleared gate. Shared tooling and the existing
audit index remain unchanged; do not mark old findings resolved automatically.

The production census checked 300 lessons (100 per band), each with four
demonstrations and one query: zero ambiguities against the five declared
rival functions in production order or in 1,500 held-out-pair rotations.
A separate seed-0 enumeration covers all four cyclic starts per band:
12 overlapping lessons, 60 pair slots, 22 unique inputs and 60 rotations.
It also found zero declared-rival ambiguities.

## Known limits and future work

Production's partitioned boxes are a deliberate safe subset. Diagonally
touching same-color components are not emitted, so a rival using eight-neighbor
connectivity is answer-equivalent on generated support; a handcrafted authority
regression checks four-neighbor semantics without claiming sampled support.
Production always includes a component needing additions and erasures, so
whole add-only or wholly unchanged scenes are accepted by the validator but
not emitted as complete default scenes. Normal generation uses 2–4 objects;
single-object validation is not a claim of single-object generation.

The scans are finite, and the large support scan uses independent Python
predictions except for its explicitly Racket-labeled witnesses. The five named
rivals do not represent every possible hypothesis. Exact override lessons are
not claimed automatically identifiable. The source remains unapproved pending
the normal maintainer process and the unresolved generic lint decision.

## Reusable entry points

- `tests/test_outline_regressions.py`: canonical, fixed-point, collision,
  exact-control, shared-color and actual-authority regressions.
- `workspace/probe_outline_support.py`: portable default/joint support census,
  dynamic declared-rival checks, source hashes and optional Racket witnesses.
- `workspace/prove_lawful_endpoints.py`: explicit lawful endpoint labels and
  negative controls for the generic lint question.
- `counterexamples/baseline-frame-interference-seed503-index26.json` and
  `counterexamples/repeated-color-box.json`: exact retained witnesses.
## Current reviewer considerations

Source SHA-256: `e8d40d9158ab2f44ad2a3964d4cebf835bfea909effebcd8c6ce1573ba2a970f`.

# Decisions — e3f72a0f2ebb

Final generator: `e8d40d9158ab2f44ad2a3964d4cebf835bfea909effebcd8c6ce1573ba2a970f`.
The selected Racket authority is unchanged. This is one per-component
transformation, not a newly composed rule family.

## R1: Admit lawful fixed points

The baseline required every component to differ from its bounding-box outline.
Its original rationale is unknown. That restriction rejected a labeled
canonical input and excluded legitimate singletons, lines, thin rectangles and
complete frames. The new validator accepts them, including a one-object scene.
The regression suite uses both isolated and companion-object cases and actual
Racket labels. Requiring every input object to change was rejected because it
changes the task domain to suit a diagnostic assumption.

Normal generation still emits 2–4 objects. This makes the distinction between
validator acceptance and production sampling explicit rather than treating
an admitted endpoint as proof of emitted support. The remaining generic
`defect_lint` warnings are retained for maintainer review. No warning
suppression or shared-linter change is included.

## R2: Reserve output geometry during construction

The baseline checked input pixels against nearby occupied pixels. That does
not protect bounding-box borders, as the saved medium seed 503/index 26 input
demonstrates: frames of colors 8 and 2 meet at zero-based (4,6).
The repair first partitions the canvas into separated whole rectangles.
Two-object scenes use strips; three/four-object scenes use a 2×2 partition.
Random cuts, object assignment, local positions and shape choices maintain
variation. Even the smallest advertised canvas has room for every requested
object without dropping one.

Retry-until-fit placement was rejected because failure/censoring can depend on
the requested counts and dimensions. Permitting competing output colors would
require an explicit rule for ownership that this canonical task does not teach.
The chosen domain excludes overlapping component boxes and does not generate
diagonal-touch same-color cases. Its safety is a support restriction, not a
claim to cover the full executable Racket domain.

## R3: Make exact controls truthful

Only `grid_h` (7–18), `grid_w` (8–18), `n_blobs` (2–4) and
`n_distinct_colors` (1–4) are advertised as exact axes. The observer derives
dimensions, orthogonal component count and foreground palette size from pixels.
Integers are required; booleans, floats, strings and out-of-range values are
rejected. Explicit color/object count pairs with more colors than objects are
declared incompatible. A color-count-only request adjusts the default object
minimum so it works independently, including four colors in easy mode.

The old palette/texture/corner/asymmetry controls were mostly unused or
misleading. Their undocumented original rationale is unknown. Retaining them
as accepted no-ops was rejected: callers now get an explicit error for retired
or unknown keys. The legal finite joint scan and shared override gate measure
this contract instead of relying on metadata assertions.

Every difficulty band retains the full legal axis domain. Even schedule phases
favor canonical dimension/palette-cardinality profiles, with enough randomness
to vary layouts and colors. Hard mode no longer excludes canonical profiles.
Making all hard grids large or satisfying the floor only through a special
nonproduction probe was rejected. Difficulty is a sampling preference, not a
different semantic rule.

## R4: Teach component identity and the actual edit

A per-color bounding-box shortcut fits all four labeled canonical pairs,
because their objects have different colors. The baseline reinforced that
shortcut by always assigning distinct colors. Odd phases now use repeated
colors on disconnected components and include a component unchanged by the
rule. A primary shape in every phase requires both added border cells and
erased interior cells. These roles refute, respectively, `color_box`,
`drop_fixed_points`, `identity`, `solid_boxes` and `add_frames`.
Colors 1–9 remain interchangeable, and neither numeric color rank nor one fixed
foreground value identifies an object role.

The four-phase schedule declares four demonstrations. Any five consecutive
pair slots contain repeated-color/fixed-point witnesses that remain among the
four demonstrations under each one-pair holdout. Relying on rare independent
sampling of the decisive witness was rejected. The actual production assembly,
not just isolated grids, was checked in 300 seeded lessons and in a fixed-seed
enumeration of every phase. All declared-rival production and rotation checks
were unambiguous.

That claim has precise limits: five distinct rival functions were tested;
there is no universal uniqueness proof. Default scenes always need additions
and erasures, so the complete population does not include unchanged or
add-only scenes. Eight-neighbor grouping is equivalent on the sampled
partitioned support; the standalone diagonal-touch authority test does not
change that. Future work could broaden these populations while retaining
enough examples to distinguish the same rivals. It would require another
source-bound census, not a prose claim.

## Evidence and reproducibility choices

The support tool discovers actual rival declarations rather than maintaining a
second name list. It separates independent Python predictions from Racket
labels, reports exact draw populations and unique inputs, retains failures,
refuses to overwrite evidence and records source hashes. Canonical
dimension/palette-cardinality hits and exact dimension/color-set hits have
separate names; the intermediate report is retained as intermediate.

The first endpoint tool's error path was found during independent review and
repaired locally. Its purpose is to publish source-bound evidence even when
the public authority or validator raises. Existing successful endpoint evidence
remains valid; the new tool's failure-injection evidence records the behavior
change. These are evidence utilities, not alternate authorities.

The initial portable test preflight failed because pytest existed only in the
user site. A clean virtual environment was created offline from installed
distribution files; its versions, origins and probe are retained. The same
expanded 65-test source was run against a disposable baseline, producing
55 failures/10 passes, then against the repaired generator, producing 65 passes.
The frozen original fixture, catalog, assignments, shared helpers and audit
index were not edited.

Review and audit work is complete. Acceptance still needs attention because
the required strict lint gate is not fully green. The lawful endpoint proof
supports an explicit shared-tool decision; it does not justify silently
marking the source approved or discarding the failed after report.
