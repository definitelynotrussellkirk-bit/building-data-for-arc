# Working notes: 579f1e2dcb4a

## Current contract (2026-10-08)

The rule finds every nonzero **4-connected** component, crops each component to
its tight bounding box, sorts crops by the component's original `(left, top)`
position, and packs them left-to-right, top-aligned, with one zero column between
adjacent crops. The canonical Racket authority was not changed; the generator
pins `RULE_HASH = "29c3632de610"`.

Final reviewed generator: version `2.0.0`, SHA-256
`3a85cb419ae1fcb64d626cf6961405cbaf432ed757e67e2bdea3e373fe3b17bb`.

## Repaired defects

The baseline generated three monochrome objects with four colors and exposed
several singleton/dead axes. That distribution could not reproduce any of the
five canonical palette/shape profiles, rejected all five canonical inputs in
`self_check`, accepted unknown overrides, and had no executable lesson-rival
contract. The before battery therefore finished with 5 green, 1 advisory, and 6
failed stages (`checks/before/checks/579f1e2dcb4a_before_battery_summary.json`).

The repair replaces those nominal axes with one exact, observable
`scene_profile` axis over the five canonical `(height, width, palette-count)`
profiles. Each profile produces sparse, multicolor 4-connected components. The
palette-6 profiles intentionally create four components: two multicolor objects
plus two same-color pieces tied on the same left edge but separated vertically.
That canonical tie is not a defect; it teaches both 4-vs-8 connectivity and the
secondary top-row ordering key. Palette-7 profiles contain three multicolor
components.

## Teaching and verification decisions

Three demonstrations are required. Eight pure rivals cover monochrome
segmentation, 8-connectivity, top-first ordering, reversed ordering, color
ordering, solid bounding boxes, bottom alignment, and missing gap columns.
`lesson_identifiable` requires the demonstrations to refute every declared rival
that would change a query answer.

The final source passed all 12 battery stages, 25/25 focused task tests, and a
100-lessons-per-band source-bound census: 300/300 lessons materialized, 1,200
query rotations checked, zero declared-rival ambiguities, and 1,199 unique
inputs. Evidence is in `checks/after-1/`, `checks/task-tests/result.json`, and
`checks/lesson-census-final.json`.

## Known limits and open findings

The generator deliberately stays inside the five observed canonical dimension
and palette profiles rather than claiming an unsupported larger domain. Its
motif grammar is compact, and the finite rival set plus random census do not
prove identifiability against every imaginable hypothesis. No source-bound
failure remains in the required checks; broader motif diversity is a possible
future extension only if it preserves the canonical 4-connectivity/tie cases.

The associated historical-note file contained no task-specific repair lead, so
this review relied on the pinned baseline, canonical pairs, and fresh battery
measurements rather than an unintegrated prior return.
## Current reviewer considerations

Source SHA-256: `3a85cb419ae1fcb64d626cf6961405cbaf432ed757e67e2bdea3e373fe3b17bb`.

# Decisions — 579f1e2dcb4a

Final generator SHA-256:
`3a85cb419ae1fcb64d626cf6961405cbaf432ed757e67e2bdea3e373fe3b17bb`.
The canonical Racket source was not modified.

## D1 — Bind implementation to the executable rule

**Choice.** Segment all nonzero cells by 4-neighbor connectivity, crop each
component, sort by `(left, top)`, and pack top-aligned with one zero column.

**Why.** All five canonical pairs match this rule, and the final Python mirror
matches every canonical output. The palette-6 examples prove that same color does
not imply one object: two pieces share a left edge and need the top-row tie-break.

**Rejected alternatives.** Per-color segmentation, 8-connectivity, top-first or
color ordering, solid bounding boxes, bottom alignment, and zero-gap packing.
Each is retained as a named executable rival rather than merely listed in prose.

**Evidence.** Focused canonical tests and
`checks/after-1/checks/579f1e2dcb4a_after_semantic_gate.json`.

## D2 — Replace nominal axes with one observable five-profile axis

**Prior choice.** The baseline advertised several axes whose values were
singleton, dead, or not observable and generated only four-color monochrome
scenes.

**New choice.** `scene_profile` is the sole public override. Its five values bind
exact canonical `(height, width, palette-count)` profiles:
`8x13/p6`, `9x12/p6`, `9x14/p7`, `10x15/p6`, and `11x16/p7`.
Every five consecutive sample indices visit every profile once.

**Why.** This makes the promised control exact and replayable, reaches every
canonical profile, and avoids inventing unsupported ranges.

**Rejected alternatives.** Arbitrary dimensions/palette sizes (unsupported),
separate height/width/palette axes (many incompatible combinations), and keeping
fake texture/density labels (not observable).

**Failure modes/limits.** The schedule is deliberately narrow. It should be
expanded only with evidence that new profiles remain lawful and teach all rule
axes.

**Evidence.** 60/60 exact profile-floor hits and 540/540 accepted override draws
in the final battery.

## D3 — Preserve the canonical palette-6 four-component tie case

**Choice.** Palette-6 scenes contain two bicolor components plus a one-color
split motif whose two 4-components share a left edge but have different top
rows. Palette-7 scenes contain three bicolor components.

**Why.** This reproduces the canonical component topology and makes both
4-vs-8 connectivity and `(left, top)` sorting necessary.

**Rejected alternative.** “Repair” all scenes to exactly three components. A
red test demonstrated that this would contradict the actual palette-6 canonical
examples; the test was corrected before implementation. The retained red log is
`checks/tdd-red-canonical-correction.log`.

## D4 — Fail closed on overrides

**Choice.** Unknown keys, non-string profile values, and unknown profiles raise
rather than silently changing or ignoring generation.

**Why.** The baseline accepted unknown controls, making replay and audit claims
unreliable.

**Evidence.** Focused tests plus the final override stage. `AXES` is an AST-literal
mapping because the repository linter validates declared controls statically;
the first dynamic equivalent failed and is retained in
`checks/tdd-red-literal-axes.log`.

## D5 — Require three demonstrations and executable rival rejection

**Choice.** Use three ordered demonstrations and one query. Declare eight pure,
deterministic rivals and require `lesson_identifiable` to refute each rival on the
demonstrations whenever it predicts a different query.

**Why.** Correct individual labels do not ensure that a lesson teaches the
intended rule. Three profiles provide enough independent evidence for the known
shortcut family without bloating the lesson.

**Rejected alternatives.** One or two demonstrations (too easy for ordering or
segmentation shortcuts), prose-only counter-hypotheses, and treating the small
battery smoke sample as sufficient coverage.

**Evidence.** 300/300 production lessons and 1,200/1,200 query rotations had zero
declared-rival ambiguities in `checks/lesson-census-final.json`.

## D6 — Keep the authority unchanged

**Choice.** Repair only the generator, focused tests, task notes, and summary.

**Why.** The Racket rule consistently labels canonical and generated lawful
inputs; defects were in distribution, validation, override contracts, and
teaching evidence, not authority semantics.

**Evidence.** Rule-smoke, Racket-lint, and authority-sync stages are green; rule
hash `29c3632de610` remains pinned.

## Native parametric return — 2026-10-24, review-9ace6b418a23cbbe

Production remains version `2.0.0` with SHA-256
`3a85cb419ae1fcb64d626cf6961405cbaf432ed757e67e2bdea3e373fe3b17bb`.
The new task-local prototype is `workspace/parametric/native_family.py`;
its thin adapter, sampler, protected audit, exact canonical resource and native
promotion contract are beside it. The canonical default is byte-for-byte
SHA-256 `29c3632de610b7ee7d934b7b3251e244cc47e7d1d119a233e359d0711def0733`.

### Rule choice and meaningful dependency

`pack_order` has three settings: `spatial`, `anchor_color_ascending`, and
`anchor_color_descending`. The alternatives select the largest nonzero
four-connected component by occupied area, derive its unique modal color from
its own cells, then rank components by their counts of that color. Count ties
retain ascending `(left, top)` order in both directions. All settings pack
original rectangular crops, top aligned with one zero gap column.

Raw crops intentionally retain foreign components inside a bounding box; the
canonical source does not mask them. The new third demonstration makes that
distinction observable. The shared grammar admits 2–6 components, singletons,
nonanchor area ties and nested bounding boxes, while requiring a unique largest
component, its unique mode, and packed width at most 30. Counts are independent:
3–6 demonstrations and 1–4 queries. Full six-plus-four banks are constructed
before prefix selection, with local RNGs and bounded duplicate retries.

The four-query sequence reaches two components, canonical-like diagonal splits,
six components, and substantive 30×30 input/output packing with 460 occupied
input cells. Input banks are matched across settings. A separate strict public
exporter exposes only visible demonstrations and the current query input.

### Repairs made before qualification

An alternate-program parenthesis defect was repaired before execution passed.
Seven targeted red regressions then exposed an endpoint/dimension mistake in
the audit rivals: Racket `bbox-of-cells` returns inclusive endpoints. Corrected
helpers now select by geometric dimensions, crop to the right size and respect
input boundaries. The retained red evidence is
`checks/579f1e2dcb4a/native-bbox-red-command.json` and its JUnit file.

The reused audit's four-pair canonical guard was adapted to this task's five
pairs with a retained red test. A separate Python-only inspection found that
seed 17's teaching palettes allowed a minimum-color rival to agree on both all
visible demos and all checked queries: a support alias, not a demonstrated
query ambiguity. Constructive D0/D1 palettes now put the modal color on opposite
sides of the other anchor color numerically. The before/after facts are in
`checks/579f1e2dcb4a/palette-teaching-repair.json`; final protected evidence
refutes both numeric shortcuts on the demonstrations.

### Executed checks and handoff

- **57 focused tests passed:** 43 adapter and 14 audit tests, including the seven
  bbox regressions, literal raw-crop/connectivity fixtures, count-prefix/RNG
  contracts and negative public-export checks.
- **Protected teaching audit passed:** seeds 0 and 17, all five canonical pairs,
  42 generated labels, 190/190 candidate comparisons refuted on the first three
  demonstrations, zero surviving rivals or execution failures, and 24 verified
  public query files. This used 509 uncached protected evaluations.
- **Native qualification passed:** three settings, six jobs, three demos/four
  queries, 78 protected evaluations. The native inventory is
  `workspace/parametric/evidence/manifest.json`; qualification/execution are
  `checks/579f1e2dcb4a/qualification/` in the review return.
- **Causal witness replayed:** two seed-0 D2 cases change only the intermediate
  color expression from component mode to raw-crop mode. The same selected
  anchor has own histogram 6:5, 7:4, versus raw-crop histogram 6:7, 7:8.
  Substituting color 7 for 6 changes 27 cells for ascending order and 52 for
  descending order. The input, selected component, downstream counting/sorting
  and packing code remain fixed. See `checks/579f1e2dcb4a/causal/`.

The result is reviewer **ready**, with no unresolved MAIN check failure. These
are finite tests and finite rival coverage, not a universal identifiability
proof. Next useful action: integrate the exact source and perform the owner's
native qualification/acceptance replay. Owner acceptance and training admission
were not performed in this reviewer workspace. Do not refresh inventory files
or alter bound source after qualification without requalifying.
