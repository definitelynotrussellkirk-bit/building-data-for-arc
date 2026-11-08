# Current notes: e521d16d403e

## Native candidate prepared October 24, 2026

The separate native adapter now supports three episode-fixed `selection_rule`
settings: `occupied_cells`, `bbox_area`, and `occupied_anchor_partner`. The first
two reuse the retained prototype's exact guarded programs. The composed setting
selects the occupied-cell winner, binds its observed color, then crops its unique
disconnected same-color partner. Its wrong-area-anchor counterfactual changes
the color and final answer; two cases passed protected Racket replay.

The constructive sampler supports 2–6 demonstrations and independently 1–4
queries. Settings share identical input streams. Four-query scenes are 14×18,
22×24, 30×30 and 26×30; the retained seed-17 30×30 scene has 185 nonzero cells,
substantial objects in all quadrants and edge contacts. The first two demos
reverse rank/order, tall/wide roles and partner size/location. This corrects an
initial support confound in which a wide-object shortcut matched the count
winner. The new aspect regressions failed before the repair and passed after.

Current finite evidence: 38 focused tests passed; 30 setting/count episodes over
seeds 0 and 1, demos 2–6 and four queries yielded 810 rival comparisons and zero
demo-fitting/query-disagreeing rivals. Native qualification passed all three
settings on seeds 0 and 17 (six jobs, three demos/four queries). See return
`checks/e521d16d403e/qualification/{qualification,execution}.json`,
`checks/e521d16d403e/self-audit.json`, `checks/e521d16d403e/sequential-witness.json`
and `checks/e521d16d403e/sequential-replay.json`. Source inventory and compact
check references live in `workspace/parametric/evidence/manifest.json` and
`workspace/parametric/evidence/current/validation.json`.

The legacy public writer hashed compact JSON but saved different pretty-printed
bytes. Its exact-byte regression reproduced the defect; both public writers now
hash and save the shared canonical serialization. Native public examples expose
only the first masked query, while all four labeled queries remain private.
`public_turn` preserves exactly the same first turn when one query is requested.

Status: **reviewer ready, owner native acceptance pending**. The selected
production generator and canonical authority remain unchanged. The owner must
qualify and accept the exact integrated source; no training admission is granted.
Limits: finite declared rivals/seeds, separated bboxes, unique winners and exactly
one partner per main anchor. No universal uniqueness, arbitrary-grid partner
uniqueness, or downstream learning benefit is claimed. Outside the generated
grammar the partner rule falls back to the anchor when missing and selects the
first partner when several exist. Current usage and commands are in the native
workspace README; retained legacy fixture evidence keeps its original scope.

Final reviewed production source: version `4.1.0`, SHA-256
`b012fe138cc2497dc1615e75815a0fc1f05cb5577e5f162cfc942702f8ec685f`.
The canonical Racket authority remains unchanged at rule hash `9d224076bec5`;
canonical source SHA-256
`2119340b5d5b36791ddb26b8488686ab3e370eedcac4069d814914d8bc260cc6`.
Detailed counts, commands, limitations, and audit-only findings are in the
return-root `REVIEW.md`, `DECISIONS.md`, `RESULTS.json`, and `AUDIT.md`.

## Intended rule and selected domain

Objects are same-color four-connected components. An object is eligible when
its tight bounding box is wider than one and every raw bbox pixel equals its
left-right reflection. Among eligible objects, choose the unique maximum by
occupied-cell count and return its exact bbox crop. Size is not bbox area.

The executable Racket program also has fallback/tie behavior. Generation
intentionally excludes no-eligible and tied-winner cases. `self_check` describes
the **selected curriculum**, not the complete executable-rule domain: it now
also requires at least one noneligible distractor component.

## October 22, 2026 repair

The pinned baseline was integrated version `4.0.1`. Prior return
`review-ad0097f547b58967:v0001` was used as a lead because it retained a
`bottommost_lr` lesson shortcut; all conclusions were remeasured on the pinned
source.

### Bottommost canonical shortcut

`bottommost_lr` fits all eight labeled canonical pairs: after filtering for
eligible LR-symmetric objects, it returns the object with the lowest bottom row.
It ignores the intended occupied-cell ranking. The current generator declares it
in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`.

Profiles 0 and 2 now place a smaller eligible decoy strictly below the true
winner. Profiles 1 and 3 preserve the complementary ordering. Thus each four-
pair schedule window contains two bottommost refutations, and every one-query
holdout leaves one among the three demonstrations. The exact current default
witness is retained at
`counterexamples/bottommost-lr-repair-witness.json`; its public Racket receipt
is `checks/selected/bottommost-racket.json` in the return.

### Reversed validator decision

The earlier notes allowed lone eligible-only grids and treated the shared
minimal-impostor warning as a false positive because such grids are lawful for
the Racket program. That was too broad for this generator's checker contract:
every exported canonical/default/explicit scene already includes a noneligible
distractor. The new choice narrows `self_check` to the actual selected
curriculum. Lone horizontal, square, and solid eligible-only grids remain valid
Racket inputs but are outside this generator's admitted training domain.
Touching different colors and diagonal fragments remain lawful when a
noneligible distractor is present.

### Strict call arguments

`generate` now requires exact integers for `seed` and `sample_index`, and a
nonnegative sample index. Booleans and floats are rejected rather than silently
aliasing deterministic streams. Axis validation remains exact and unknown
controls fail explicitly.

## Four-profile teaching schedule

The default profile is `(seed + sample_index) % 4`.

| Profile | Main geometry | Selection witnesses |
|---:|---|---|
| 0 | 10×10; six-cell 2×4 winner above a lower five-cell 3×3 cross; width-one bar; larger asymmetric block | occupied cells vs bbox area; width-one exclusion; bottommost refutation; answer rank three |
| 1 | Compact families with eligible scan order reversed | first/last order reversal; same size/eligibility witnesses |
| 2 | Broad winner above a lower smaller eligible decoy; larger asymmetric object; disconnected same-color L | bottommost refutation; component vs color grouping; larger ineligible object |
| 3 | Broad families with eligible order reversed | first/last reversal and the same broader object-role evidence |

Lessons use three ordered demonstrations and one query. The declared rival set
contains ten rules: `largest_object`, `second_largest_object`, `first_lr`,
`last_lr`, `smallest_lr`, `largest_bbox_lr`, `bottommost_lr`,
`width_one_allowed`, `either_axis`, and `group_by_color`. Eight of these fit all
usable canonical labels; `largest_object` and `second_largest_object` do not.

Final finite evidence at the source hash above:

- portable task tests: 69/69;
- strict battery: 12/12 green;
- cyclic task-local scope: 48/48 production windows and 192/192 query rotations
  refute every declared rival;
- production census: 300/300 lessons, 1,200 pairs/unique inputs, zero production
  ambiguities and zero ambiguities over 1,200 rotations.

These results do not establish unique induction against undeclared hypotheses
or downstream model performance.

## Exact controls

The supported integer axes remain:

| Control | Range | Pixel-observable meaning |
|---|---:|---|
| `grid_h`, `grid_w` | 10..22 | returned dimensions |
| `sym_h` | 2..6 | winning bbox height |
| `sym_w` | 2..7 | winning bbox width |
| `n_asym` | 1..3 | noneligible component count |
| `n_sym_decoy` | 0..2 | other eligible component count |

Any explicit control selects the constructive exact layout and honors the full
advertised joint domain. Explicit layouts are lawful but do not inherit the
default ordered curriculum's anti-shortcut guarantee.

## Proposed parametric family

`workspace/parametric/` contains a separate, runnable, **unapproved** prototype
with `selection_metric ∈ {occupied_cells, bbox_area}`. The canonical/default
setting is guarded byte-for-byte; the alternative changes only the comparator.
Two episodes exercise both settings using exact Racket labels. It is not part of
production generation, catalog metadata, or training approval.

## Known limits and open findings

- Fallback/no-eligible and tied winners are not taught.
- Generated bboxes are separated, so nested/contaminated/touching configurations
  are validator edge cases rather than normal curriculum support.
- The ten-rival checks are finite and cannot certify every plausible shortcut.
- The legacy prototype entrypoint retains four authored scenes and two old seeds; the separate native adapter and current evidence above extend that scope.
- Audit targets `e58b545527d3` and `67702540cb95` were not edited; see return-root
  `AUDIT.md`.

## Current owner source and evidence limits

Accepted the bottommost-object rival and two refuting profiles, exact scalar guards and an explicitly narrower curriculum validator requiring a distractor. The unchanged Racket rule supports additional fallback and tie cases outside that curriculum. The reviewer reports 12 green stages after resuming an external interruption, 69 portable tests, and fresh full-extraction replay of 96,709 files with 37 regressions, 10 prototype tests and 69 portable tests passing. The census has 300 lessons and 1,200 clean rotations; a separate four-seed check covers 48 windows and 192 rotations. An unsupported replay phase failed before tests and is retained. The occupied_cells/bbox_area prototype has two episodes, 42 Racket applications and eight canonical checks. Separately, the owner corrected public filenames, passed two focused regressions and regenerated both episodes. Original source and reports remain separate. Overrides do not inherit the default teaching guarantee. No variant or training approval.
## Current reviewer considerations

Source SHA-256: `b012fe138cc2497dc1615e75815a0fc1f05cb5577e5f162cfc942702f8ec685f`.

# Decisions: e521d16d403e

All production decisions below are bound to generator SHA-256
`b012fe138cc2497dc1615e75815a0fc1f05cb5577e5f162cfc942702f8ec685f`.
The exported lesson policy is three ordered demonstrations plus one query from a
four-profile schedule; every single-query rotation is required to remain
identifiable against the declared rival set.

## D1 — Keep the canonical authority unchanged

**Choice.** Retain the exact rule: same-color four-connected components,
width-greater-than-one raw-bbox left-right symmetry, rank eligible components by
occupied-cell count, and return the winner's tight crop.

**Rationale and probe.** Rule smoke, authority sync, all eight canonical labels,
and the public bottommost witness bind the selected generator to rule hash
`9d224076bec5`. No evidence justified changing labels or Racket semantics.

**Alternative rejected.** Changing the authority to match a positional shortcut
would preserve the wrong reason and invalidate canonical provenance.

**Limit.** Racket fallback/tie behavior is broader than the selected curriculum.

## D2 — Repair the strongest observed canonical shortcut in the curriculum

**Prior choice.** Version 4.0.1 varied scan order, size rank, bbox area, width-one
eligibility, and color grouping, but did not declare or reliably refute
"choose the bottommost eligible symmetric component." A prior audit return was
used as a lead, not as current-source proof.

**New choice.** Declare `bottommost_lr`; in profiles 0 and 2 put the smaller
eligible decoy strictly below the occupied-cell winner. Profiles 1 and 3 retain
the complementary ordering, so each four-pair window has two refutations.

**Probe.** `counterexamples/bottommost-lr-repair-witness.json` is a current
default draw with exact Racket and rival outputs. `checks/lesson-windows-after.json`
checks every cyclic start and every one-query rotation for seeds 0/1/17/37 in
all bands. The 300-lesson census independently tests the production sampler.

**Alternatives rejected.** Removing lower decoys would hide the shortcut rather
than teach against it. Random resampling until a witness appears would weaken
replayability and could still leave bad complete lessons.

**Failure modes/limits.** Ten executable rivals are not all possible induced
rules. The claim is finite, source-bound coverage, not universal learnability.

## D3 — Reverse the lone-object validator decision

**Prior choice.** The earlier notes treated lone eligible-only grids as lawful
because the executable Racket rule handles them and argued the shared
minimal-impostor warning was a false positive.

**New choice.** `self_check` is explicitly the **selected curriculum validator**,
not the full Racket domain. It now requires at least one noneligible distractor.
Every canonical input and every exported default/explicit construction already
has such a distractor, so the narrowing aligns the checker with actual training
support instead of rejecting a sampled case or changing the authority.

**Probe.** New fail-first tests reject lone horizontal, square, and solid
eligible-only grids; companion tests retain touching-color and diagonal-fragment
cases when a distractor is present. The focused defect lint and final battery
are green.

**Alternative rejected.** A task-local linter waiver would preserve a mismatch
between the claimed selected curriculum and its checker. A blanket Racket-domain
validator would be useful for another purpose but is not what this generator
exports.

**Limit.** Lone eligible objects remain valid inputs to the unchanged Racket
program; they are simply outside this generator's admitted curriculum domain.

## D4 — Enforce strict call scalars

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, and
`sample_index >= 0` before creating `GenCtx`.

**Rationale.** Boolean and floating-point aliases can collapse deterministic
streams or create undocumented schedules. The before linter reproduced 27
accepted-invalid-scalar warnings across easy/default/hard calls.

**Alternatives rejected.** `int(...)` coercion would silently merge distinct
caller inputs. Deferring validation to lower layers leaves direct generator
calls inconsistent.

**Probe/limit.** Focused tests cover booleans, integral/nonintegral floats, and a
negative index. Very large exact integers remain accepted by design.

## D5 — Prototype one small rule parameter, separate from production

**Choice.** Build `selection_metric ∈ {occupied_cells, bbox_area}` under
`workspace/parametric/`. The canonical/default setting is guarded by a full
byte-for-byte source hash; the alternative changes only the eligible-object
comparator. One setting is selected once per episode.

**Why this parameter.** It preserves object roles, connectivity, symmetry test,
and crop operation while creating a meaningful, locally checkable rule family.
Four lawful scenes reverse occupied-size and bbox-area ranking, so three demos
identify the setting before the masked query.

**Alternatives considered.** Parameterizing symmetry axis or connectivity would
change more of the reasoning structure and require a broader input redesign.
Adding arbitrary palette/output changes would be cosmetic rather than a rule
parameter.

**Probe.** Two episodes exercise both settings; exact Racket executes 42 times,
including deterministic replays and all eight canonical labels. The parameter
rival is refuted in every episode. Evidence is under
`checks/parametric/selection-metric-v1/`.

**Limit/status.** This is **proposed and unapproved**. Four authored inputs and
two seeds do not establish general support, and no catalog/training path selects
the variant.

## D6 — Keep exact controls separate from lesson claims

The six integer controls remain grid height/width, winner bbox height/width,
noneligible-component count, and smaller-eligible-decoy count. Explicit controls
use the exact constructive layout and are pixel-observable. They are not promised
to preserve the ordered four-profile curriculum; for example, requesting zero
eligible decoys removes a key selection witness. Unknown controls and invalid
scalar types fail explicitly.

## D7 — Audit without editing the two drawn targets

`e58b545527d3` and `67702540cb95` were inspected at their pinned source hashes.
Concrete evidence is retained in `checks/audit/` and summarized in `AUDIT.md`.
Per assignment scope, neither target generator was modified and no audit finding
is presented as approval or as a completed repair.
