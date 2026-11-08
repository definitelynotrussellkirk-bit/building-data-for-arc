# f9cd85012aa8 — current generator account

VERSION 3.1.0. Rule authority remains canonical `35becc0ed855`; no Racket or
canonical-data change. Find the sole 4-connected sparse color-6 component,
fill its bounding rectangle with 6, and erase everything else on a same-size
zero canvas. Generation constructs inputs; the canonical Racket executor
supplies labels. Python output construction is confined to semantic rivals.

## Domain and exact controls

Legal grids contain literal Python integer colors 0..9, one sparse connected
6-component, and distinct-colored non-6 components outside its 8-neighborhood.
Other components may touch each other if their colors differ. The validator
checks these conditions and rejects Boolean/fractional cells.

The supported exact axes are `grid_h=5..20`, `grid_w=6..24`,
`shape_size=3..10` (number of 6 cells), and `n_distractor=0..4`
(same-color 4-connected component count). `None` means the default draw;
invalid scalars and unknown keys fail clearly. `sample_index` must be a
nonnegative Python integer. The formerly advertised palette, density,
position, and texture controls were removed because the baseline ignored
them; callers must migrate instead of relying on silent no-ops.

Any non-None override selects the compact constructive population. A sparse
target of at most 3×4 can always be placed on the minimum 5×6 canvas with at
least six positions beyond its 8-neighborhood. This proves room for all four
distinct-colored singleton distractors across the advertised product. Bounded
random growth and an exact-count fallback replace the old fixed tetromino
fallback. `observe_overrides` exposes measurements; the joint-axis probe also
counts pixels and connected components independently.

## Default lesson population

`EXAMPLES_NEEDED=7`, `LESSON_SCHEDULE_PERIOD=8`. Every default eight-pair window
alternates four canonical core slots and four rich scenes. The three core
signatures are (rows, columns, target pixels) = (7,8,4), (8,9,4), (9,10,5),
with palette {0,6} and no distractors. Geometry and placement vary; core slots
are not four distinct canonical profiles. The strict floor remains 25%.

Rich scenes have two sparse distractors. Default dimensions vary by band:
easy 17–18×6–8, medium 18–19×7–10, hard 19–20×9–12. The vertical placement
construction is a deliberate distribution restriction, not part of the rule.

| Residue | Target pixels | Target bbox area | Count rank | Area rank | Color rank | Scan rank |
|---|---:|---:|---|---|---|---|
| 1 | 7 | 16 | low | high | high | middle |
| 3 | 7–8 | 12 | middle | middle | middle | first |
| 5 | 9–10 | 15 | high | low | low | middle |
| 7 | 8 | 20 | middle | high | middle | last |

There are 21 executable canonical shortcuts, shared by identity with lesson
competitors and semantic rivals. They include min/max/median selection by
pixel count, box area, scan order, numeric color and aspect ratio; fill-all,
keep-distractors, three/four-cell caps, and the unique-area-12 shortcut.
Every declaration fits all three labeled canonical pairs. Each complete
default eight-pair window supplies at least two refutations of every listed
rival, so one held-out query leaves a refutation among the seven demos.
`lesson_identifiable` scores the actual supplied labels; it does not infer
success from a seed or schedule position.

## Reversed decisions and retained evidence

The baseline 2.0.2 advertised controls without applying them, used a
size-changing fallback, and supplied no executable lesson contract.
Earlier audit leads were `review-3f97e96eb4741d55:v0001/v0002` and
`review-a7304ba015dd369f:v0001`; findings were remeasured on the pinned source.
This repair does not manually close retained audit records.

An intermediate six-slot schedule made every rich target bbox area 12 and
oversampled large grids. Independent review found that color-blind shortcut;
the retained area-12 witness documents it. A later eight-slot revision still
let the most elongated object predict all but one scene. Changing the last
nine-cell distractor from a 5×5 to a 3×5 box supplies a second refutation and
breaks the earlier deterministic relationship between target count and area
ranks. Both failed revisions and their regression results remain in the return.

## Limits and reproduction

The guarantees concern these finite alternatives, default assembly, and
single-query rotations. They do not prove unique induction or generalization
to every valid grid. Rich shapes remain bounded by five cells per side;
placements are vertically separated. Exact-override grids use singleton
distractors and do not inherit all default teaching witnesses. Difficulty
changes canvas size, not the transformation or core distribution.

Focused tests live in `tests/`. Reusable authoring tools and their commands
are documented in `workspace/README.md`; small counterexamples are under
`counterexamples/`. The review return's `REVIEW.md`, `DECISIONS.md`, and
`RESULTS.json` contain exact source-bound counts and commands, including
Racket census evidence. Training approval remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `5d56b67a76405569e229b852ae2b6af7f4fc5491cf2e2a476a319437e254746e`.

# Decisions and rejected alternatives

Final source: `5d56b67a76405569e229b852ae2b6af7f4fc5491cf2e2a476a319437e254746e`.
All source edits stay within `repo/generators/f9cd85012aa8/`. The canonical
rule and both assigned audit targets are unchanged.

## D1 / R1: advertise four exact controls and honor their joint product

The baseline advertised ten axes but drew dimensions, target size and noise
from unrelated random ranges. The first compact reproduction requested a
5×6 grid, three target cells and zero distractors; it returned 11×16, five
target cells and two distractors. Prior retained audits suggested the same
problem; `checks/joint-axes-before.json` remeasures it on the pinned baseline.

The repaired controls are rows 5–20, columns 6–24, target cells 3–10 and
distractor components 0–4. Shared `draw_int_strict` handles each real axis;
`None` requests defaults, while Boolean, float, string and out-of-range values
fail. Unknown keys fail instead of silently selecting a default. The sample
index is separately restricted to nonnegative Python integers because the
shared context otherwise accepted Boolean, fractional and negative indices.

The palette, density, texture and position controls were never implemented.
Implementing ten interdependent policies would enlarge this repair and create
unclear conflicts with fixed semantic color 6. They were removed and now
raise clear unknown-key errors. This is an intentional API change, reflected
in version 3.1.0 and current notes; old callers must migrate. Degenerate
textures no longer deliberately manufacture grids outside the valid domain.

`observe_overrides` reports actual dimensions, target cells and non-6
4-components. The reusable joint probe independently measures those quantities
and replays each call for determinism. Final evidence: 960 parameter cases,
1,920 actual draws, zero failures; 320 distinct grids because fully specified
controls intentionally give the same compact draw across bands. The probe
checks dimension corners, every size/count value, seeds 0 and 7, and all bands;
it is not an exhaustive all-seed/all-dimension experiment.

## D2 / R2: constructive fallback instead of silently changing a request

The old sparse-growth fallback always returned four cells, even when asked
for another size. Random placement could also fail to place some distractors.
The replacement uses bounded random growth, exhaustive positions and an
exact-count constructive fallback. A connected sparse target with any size
3–10 fits within a 3×4 corner. On the smallest 5×6 canvas, the entire last row
lies outside its 8-neighborhood, leaving at least six available cells for
at most four different-colored singleton distractors. Larger canvases inherit
this construction. There is therefore no hidden incompatible combination
within the four advertised bounds.

This deliberately gives explicit overrides a compact population. It avoids
silently expanding the canvas, reducing an object count, or retrying forever.
Using arbitrary multi-cell noise under every minimum-size override was
rejected because it would require additional feasibility rules and change
the meaning of the existing controls. Rich multi-cell distractors remain in
the default teaching population. Forced-fallback and boundary regressions
are in `tests/test_controls.py`.

## D3 / R2: enforce the declared input domain

The validator now checks a nonempty rectangular list of rows, literal Python
integer colors 0–9, exactly one 4-connected color-6 component, a non-solid
target box, no non-6 cells within its 8-neighborhood, and distinct colors for
non-6 connected components. Same-color disconnected fragments count as
separate components and are rejected when they violate the distinct-color
condition. Differently colored distractors can touch without merging.

The validator is broader than the sampler: it does not require every valid
input to be an emitted grid or fit the exact-axis range. This is why the
hand-built 5×6 largest-object counterexample is lawful even though its
four-cell distractor is absent from the compact sampler. Domain validity,
sampler support, and teaching support are reported separately.

## D4 / R3–R4: use an eight-slot default schedule with seven demos

The old generator randomized shapes and noise without an executable lesson
contract. Correct single-grid labels did not establish that each lesson
taught color-based selection. The first repair used four rich examples plus
two core examples; the profile-floor sampler measured only 14/60 canonical
hits, below the unchanged 25% threshold. Lowering the threshold was rejected.

The final period is eight: four alternating canonical core slots and four
rich scenes. Core signatures are exactly (7,8,4), (8,9,4), and (9,10,5), in
rows/columns/target-cell notation, with palette {0,6}. Each core slot chooses
among these three signatures and varies geometry/position. Four slots do
not imply four distinct canonical profiles. Final profile support is 27/60
under the profile-floor sampler and 296/600 under the strict semantic sampler.

Seven demonstrations plus one query give a full period. Each listed rival
has at least two refuting pairs per complete default period. Removing any
one query leaves at least one refuting demonstration. A lesson hook evaluates
the actual labeled pairs, including materializer rejection effects and
overrides, rather than asserting success from the requested start index.

The cost is two more demonstrations than the first six-slot repair. This
is deliberate teaching support, not a claim that a human needs seven
examples or that seven is mathematically minimal. Randomly hoping for a
refutation, accepting ordered production without checking rotations, and
claiming an untested all-hypothesis guarantee were rejected.

## D5 / R3: vary geometry and inspect new shortcuts introduced by repair

Every rich target in the first repair had bbox area 12. The color-blind rule
“select the sole object, otherwise the unique area-12 box” fitted canonical
data and all default examples of that intermediate source. The retained
review witness showed a lawful disagreement. Target areas now vary across
16, 12, 15 and 20, with area 12 also occurring on distractors.

The next review found a different issue: selecting the most elongated bbox
fitted seven pairs and failed only on held-out residue 1. Residue 7's large
nine-cell distractor changed from a 5×5 to a 3×5 box. Its aspect ratio 5/3
now exceeds the target's 5/4, yielding a second refutation. This also changes
the last target's area rank and breaks the previous inverse relationship
between count and area ranks. Target box sides of five at residues 5 and 7
provide two four-cell-cap refutations.

| Rich residue | Target cells | Target area | Count rank | Area rank | Color rank | Scan rank |
|---|---:|---:|---|---|---|---|
| 1 | 7 | 16 | low | high | high | middle |
| 3 | 7–8 | 12 | middle | middle | middle | first |
| 5 | 9–10 | 15 | high | low | low | middle |
| 7 | 8 | 20 | middle | high | middle | last |

The contract now contains 21 unique rivals, including min/max/median aspect
selection with exact rational comparisons. Every canonical shortcut is
checked against all three canonical pairs. Namespace aliases share callable
identity, so 63 declaration bindings represent 21 alternatives. The full
Racket census measures materialized lessons, while unit tests add small
deterministic regression checks and a deliberately under-taught lesson that
must be reported as ambiguous.

## D6 / R4: reduce canvas drift and give bands an observable effect

An intermediate rich population used roughly 18–20×18–24 canvases, excessive
relative to canonical median area 72, and generated identical draws in all
bands. The final rich defaults are easy 17–18×6–8, medium 18–19×7–10 and
hard 19–20×9–12. Three separated vertical slots need only 17 rows and at most
five columns per object. Maximum default area is 240; the defect gate's
inspected area-drift threshold was 288. Canonical core grids remain shared
across bands so their distribution stays faithful to the demonstrations.

The design trades arbitrary two-dimensional layouts for reliable separation
and varied semantic ranks. Transposes/reflections of shapes and random
horizontal placements provide variation within that restriction. Rich
vertical placement, four geometry profiles and a five-cell box-side cap
remain known limitations. A future broader sampler should add witnesses
without discarding canonical support or exact-axis feasibility.

## D7: reference authority, composition and solve boundaries

No Racket rule change is justified: the measured defects concerned generated
inputs, control behavior and teaching examples. Labels in the final census
and witness pack come from the supported canonical Racket executor. Python
mirrors in tests and rival code serve authoring checks, not reference authority.

This remains a color-conditioned box-completion task. The repair adds no
sequential state or interacting transformation rules merely to increase
apparent complexity. Fixed color 6 is the selection cue. Optional curriculum
metadata limits the contextual-gating claim to the retained generated witness;
task-defined-symbol generalization remains unknown.

The blind author used only the separate task's visible examples before
generator work. The later solver honestly records prior exposure. Genuine
earlier revisions and infrastructure failures remain preserved, without
invented wrong solutions. Hidden-query correctness is withheld. The final
source, prepared challenge, program and finish notes are bound by hashes.

## D8: keep useful evidence within a compact return

The baseline override report was 51,011,720 bytes. Its lossless gzip, original
path/size/SHA manifest and verification receipt are retained under
`checks/compressed-before/`; no failure was discarded. Larger lesson reports
use the provided census gzip option. `EVIDENCE-BUNDLE` may consolidate members
but does not itself reduce the expanded-size budget.

Three small task-local probes support future reviewers: independent joint
controls, the original exploratory rivals, and a current-declaration Racket
witness pack. All public-authoring tools remain separate from visible-only
solves. Shared-tool proposals in `FEEDBACK_TO_CODEX.md` are recommendations;
no frozen shared source was edited. Final verification uses the package
builder's exact patch on a fresh original extraction, verifies every changed
path and reruns the task tests there before acceptance.

## 2026-10-25 native parametric build

Built a two-setting native family under `workspace/parametric/` without changing
the accepted production generator or canonical authority.

- `target_mode=canonical_target` emits the exact selected canonical Racket program.
- `target_mode=anchor_size_relay` adds a sequential relay: count the cells in the
  sole sparse color-6 anchor, convert that count to `(size - 3) modulo N`, then
  select the corresponding row-major non-6 object, erase the rest, and fill the
  selected object's bounding box with its own color.
- Inputs are matched across settings for each seed/count request. The supported
  API is 2–6 demonstrations and 1–4 queries; qualification uses three
  demonstrations and four queries.
- The fourth query is a substantive 30×30 construction with seven separated
  candidates and content touching all four boundaries.

The bounded teaching audit covers seeds 0 and 17 and all demonstration counts
2–6. It refutes twelve declared rivals, executes 12 labels in protected Racket,
and records a wrong-intermediate causal case where shifting the anchor-derived
selector by one changes the selected object and final grid. An initial sampler
allowed shape height to swap the two middle candidates for one seed, which let a
smallest-object shortcut fit both minimum-count demonstrations. Pinning both
middle slots to the same row band repaired the ordering leak. This remains finite
evidence, not a proof of universal uniqueness.

Verification completed in this packet:

- 73 focused parametric tests pass after the ordering repair.
- The full source-bound suite passes 185 tests.
- The copied-runtime task suite passes the same 185 tests.
- Native qualification passes both settings × two seeds, with 40 protected-Racket
  evaluations.
- The causal witness was constructed and independently replayed from the native
  qualification receipt; replacing `(anchor_size - 3)` by `(anchor_size - 2)`
  selects a different object and changes the final grid.

Evidence:

- `workspace/parametric/evidence/current/audit.json`
- `workspace/parametric/evidence/manifest.json`
- packet checks at `WORK/checks/f9cd85012aa8/qualification/` and
  `WORK/checks/f9cd85012aa8/causal/`

No owner acceptance or training admission was performed.
