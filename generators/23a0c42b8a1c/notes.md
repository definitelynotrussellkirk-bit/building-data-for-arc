# Working notes: 23a0c42b8a1c

## Current decision — review-0a7960b3204c9f47, version 3.0.0

Select the smallest same-color four-connected component cardinally adjacent
to the single color-1 marker. Crop only that component, recolor its cells 8,
and keep all other crop cells 0. Canonical Racket `5af80c67d390` is unchanged.

The previous generator always placed a fixed four-cell target above the marker,
ignored `small_size`, and rejected all three canonical one-neighbor inputs.
The repair accepts the canonical case and teaches actual minimum selection
through both reading orders, all four directions, disconnected distractors,
and foreign-cell bounding-box counterexamples. Exact dimensions, selected
size 1..7 and total color count 4..6 are realized and observable. Unsupported
axes were removed; malformed scalar arguments and unknown controls reject.
Palette names are overlapping color preferences, with a random default.

Default lessons require four demonstrations and one query. The five-pair
schedule is first/last/single/first/last; two copies of each order contrast
permit any one pair to be held out. Eight declared rivals and six executable
witnesses document the finite teaching claims. Tiny forced size overrides
are lawful but are not promised to supply the default teaching curriculum.

Exterior distractors were changed from singletons to dominoes after the
structural gate exposed loss of the canonical single-singleton marker role.
Interior singleton distractors remain to teach target-only masking. A missing
largest-neighbor witness binding was added after the semantic gate flagged it.

## Limits and open authority question

The retained Racket comparator's equal-size branch passes an object record to
a grid `top-left` accessor and raises. Even a unique minimum with tied larger
neighbors can trigger it. Generation therefore uses one or two unequal-size
neighbors; self-check requires all adjacent sizes to be distinct. Tie support
is not implemented or claimed. Public counterexamples and exact labels are
retained in this return's `checks/repair-authority/` and task counterexamples.

Shapes use a bounded 3×3 bank; two neighbors lie on opposite sides of the
marker. These are explicit support restrictions, not exhaustive task support.
Imported audit status in `evidence/review_index.json` remains unchanged; the
prior `review-f4ee04c336989569:v0001` finding was independently reproduced and
addressed in this proposed repair, pending maintainer intake.

`workspace/parametric/` is a separate proposed prototype with one episode-wide
output-color parameter {8,2}. Its two-setting evidence does not approve a
canonical-rule change or variant training distribution. See the returned
REVIEW.md, DECISIONS.md and source-bound `checks/final/` receipts for measured
counts and limitations; no model-quality improvement is claimed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f4ee04c336989569:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b377352acbc2c53089f29f91ddd2d5f3e79d45411ea3264a0bc5f2cd86acb224`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Repaired by accepted source 4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b in review-0a7960b3204c9f47. tests/test_marker_selection.py tests exact small_size=1..7 at seed 101 index 1 in every band and global dimension extrema; checks/final/battery/checks/23a0c42b8a1c_after_override_results.json reports 43920 accepted exact-control draws and zero findings. This explicitly resolves the old ignored small_size/dimension contract audit on reviewer-reported focused evidence; no maintainer rerun.

### Assessment or prior finding

## 23a0c42b8a1c

**Reproduced exact-override defect — the advertised `small_size` control is accepted but not honored.**

Generator SHA-256: `b377352acbc2c53089f29f91ddd2d5f3e79d45411ea3264a0bc5f2cd86acb224`. With seed `101`, sample index `1`, `difficulty=null`, and overrides `{"grid_h":13,"grid_w":11,"palette_kind":"warm","small_size":1}`, the generator returns a validator-clean `13×11` input (`self_check: []`) inside the documented axis domain. Its two relevant adjacent-color components have sizes 4 and 7; the requested size-1 component is absent. The authoritative Racket output contains four nonzero cells, selecting the actual size-4 component rather than anything of the requested size. Thus `small_size=1` is silently ineffective even though the override is accepted.

The exact input, component census, override values, and result are retained in `checks/audit/23a0c42b8a1c/report.json` and `checks/audit/23a0c42b8a1c/override_probes.json`. The supported Racket replay is `checks/audit/23a0c42b8a1c/racket.json` with executed rule hash `5af80c67d390`. The probe file also records a separate difficulty-bound inconsistency for an advertised `grid_h` value. No source was changed for this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-f4ee04c336989569-v0001/audit_assets.json), manifest SHA-256 `99ffcef1bbfe20717a331ace784f0b91d3fc5aa3032f13f6282c5de709f5fa87`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b`.

# Decisions for review-0a7960b3204c9f47

## Authority and scope

The assignment remains `23a0c42b8a1c`; neither audit target was substituted. The
selected canonical Racket program remains unchanged at
`5af80c67d3907183931a179f7ff8ad18fc3c41ab97c1030589b0a4649a5ca7c7`
(`RULE_HASH = "5af80c67d390"`). Generator version moves from 2.0.0 to 3.0.0.
The final generator SHA-256 is
`4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b`.

The rule extracts the smallest same-color, four-connected nonmarker component
cardinally adjacent to the color-1 marker. It crops that component to its own
bounding box, recolors its cells 8, and leaves all other crop cells 0. Cropping
all foreground inside that rectangle is a different rule. Python rival code
is diagnostic; retained reference labels come from Racket.

The existing unresolved review `review-f4ee04c336989569:v0001` was a lead, not
proof of the selected bytes. Its retained `small_size=1` reproduction exposes
the old fixed four-cell target. Fresh baseline checks and regression failures
independently confirm the old defects. Imported review indexes and unrelated
generator approval states were not edited.

## R1: restore lawful canonical support

The old self-check required multiple marker neighbors even though each of the
three canonical inputs has one. The repair accepts one or more adjacent
components with pairwise distinct sizes and requires exactly one single-cell
color-1 marker. Ordinary generation mixes one-neighbor examples with genuine
two-neighbor selection examples. This preserves the canonical case while
teaching why adjacency and size matter when a choice exists.

Self-check validates nonempty rectangular row lists, actual integer colors
0..9 (excluding Boolean values), background 0, the marker, and executable
selection. It does not force every lawful external input into the sampler's
small shape bank. Its contract is intentionally broader than ordinary sampling.

## R2: truthful, usable controls

| Control | Final support | Why |
| --- | --- | --- |
| `grid_h` | Exact integers 7..20 in every band | Fits the bounded construction; includes canonical heights 8/9. |
| `grid_w` | Exact integers 8..19 in every band | Includes canonical widths 11/12/13 and supports the smallest canvas. |
| `small_size` | Exact integers 1..7 | Fixes the ignored size control; the selected target has exactly this many cells. |
| `n_distinct_colors` | Exact total input count 4..6, including background | Measures realized colors, rather than a drawn but unused palette. |
| `palette_kind` | `default`, `warm`, `cool`, `varied`; random default | A color-pool preference with overlapping support, explicitly diagnostic. |

Seed must be an integer excluding Boolean; sample index must also be nonnegative.
Difficulty must be absent/None or one of easy, medium, hard. Invalid exact-axis
scalars and unknown override names are rejected instead of coerced or ignored.
Explicit None overrides retain the underlying GenCtx default convention.

Unused `texture`, `position_bias`, `density`, and the inaccurate duplicate
`palette_size` declaration were removed. The alternative—retaining claims for
controls that do not affect the returned input—would leave the diagnosed
contract defect in place. GenCtx choice draws and `observe_overrides` expose
the actual dimensions, target cardinality and color count. Palette names are
not claimed to be uniquely recoverable from a grid.

Dimensions are weighted toward the canonical profiles, with positive ordinary
support across the full documented ranges. Default targets have 4..7 cells;
easy favors 4/5, medium 4/5/6, and hard 5/6/7. The exact override endpoints 1/2
remain lawful simple cases, but the four-demo teaching guarantee is measured
on the default production curriculum, not on every forced override sequence.

## R3: geometry and masking

All normalized connected shapes within a 3×3 support are enumerated once in a
small deterministic bank. Exact cardinality comes from construction; there is
no clipped shape or altered-size fallback. The selected shape has missing
bounding-box cells for default sizes. A larger neighbor uses a compact shape,
which supplies cases where bounding-box area ranks objects differently from
cell count. Placement randomizes all four marker directions, retains the
scheduled reading order, and has an explicit 80-attempt bound.

In two-neighbor inputs the components are on opposite sides of the marker.
Disconnected distractors make global minimum selection wrong. Some examples
place a foreign-colored singleton in the target's bounding box, demonstrating
that the output masks the selected object instead of cropping every foreground
cell. Placement excludes marker adjacency for distractors and prevents merging
with an existing same-color component.

The first implementation used singleton distractors everywhere. The strict
structural diagnostic correctly highlighted that every generated input then
lost the canonical single-singleton marker role. Exterior distractors are now
dominoes; interior mask witnesses remain singletons. This supports both the
clear marker role and the harder foreign-cell case. The regression that
requires ordinary single-singleton support failed in all three bands before
this change and passes afterward.

## R4: four-demonstration curriculum and query rotations

The intended assembly is four consecutive demonstrations followed by one
query, using the five-pair schedule:

| Sample index modulo 5 | Neighbor configuration |
| --- | --- |
| 0 | Two neighbors, target first in reading order; foreign-cell mask witness |
| 1 | Two neighbors, target last in reading order |
| 2 | One neighbor, preserving the canonical case |
| 3 | Two neighbors, target first; foreign-cell mask witness |
| 4 | Two neighbors, target last |

Every cyclic five-pair window contains two first, two last and one single
case. Repetition is purposeful: moving any one pair to the query still leaves
both order contrasts and a mask contrast in the demonstrations. Three demos
were rejected as the default promise because a holdout can remove the only
example refuting a positional shortcut. `EXAMPLES_NEEDED=4` and
`LESSON_SCHEDULE_PERIOD=5` state the actual assembly contract.

The eight declared rivals cover first/last neighbor, largest neighbor,
smallest bounding-box area, global smallest object, retaining input color,
filling the entire bounding box, and retaining all foreground in that box.
Only the five rivals that fit every canonical pair are called canonical
shortcuts. In particular, global-smallest does not fit the canonical examples
and is not mislabeled as canonical-consistent.

Six executable witnesses are bound to their actual rival predictions. The
initial contract omitted the largest-neighbor witness binding even though
the sampler generated its counterexamples; the semantic gate caught that
omission, and it was fixed. Witness frequency alone is not treated as a
lesson guarantee: final evidence includes the strict semantic smoke test,
100 complete lessons in each band, and all five cyclic starts at fixed seed 0.
See `checks/final/`; production and query-rotation verdicts are recorded
separately in `REVIEW.md` and `RESULTS.json`.

## R5: retained reference-rule limitation

The current Racket sort comparator calls `top-left` on an object record when
component sizes tie, but the retained prelude's `top-left` expects a grid.
Fresh public applications fail on equal-size neighbors. They also fail on a
unique minimum accompanied by two equally sized larger neighbors, because
sorting may compare those larger objects. Thus rejecting only minimum ties
would be insufficient.

The selected Racket authority was not changed. Generation uses at most two
neighbors with unequal sizes, and self-check rejects every repeated adjacent
size. `checks/repair-authority/public-racket-result.json` contains three
intentional failing tie cases and four successful controls, including the
three canonical inputs. Those seven executions, not the two earlier failed
private-loader setup attempts, establish the observed tie limitation.

Extending tie support needs a separate authority decision and reference tests.
No top-left tie-breaking correctness is claimed by this repair.

## Parametric assessment: suitable prototype, proposed only

The returned `workspace/parametric/prototype.py` supplies one bounded parameter,
`output_colour ∈ {8, 2}`, chosen once per episode. Color 8 preserves the exact
canonical program; color 2 changes only the fixed extraction color. The
prototype guards the canonical source hash and executes its instantiated rule
through the real Racket bridge. Public challenges omit the parameter and
query labels; the demonstrations reveal the fixed recoloring operation.

Two complete episodes, six demonstrations, two queries, four authored input
grids, 37 real Racket applications, and the 15 focused tests are retained in
`checks/parametric/`. Both parameter settings have an output-distinguishing
witness; canonical color 8 reproduces all three supplied canonical pairs.
These are finite prototype results, not a new approved training distribution.

The direct legacy `rule_wrap` helper imports an unavailable module in this
packet. The prototype therefore uses a task-local, exact-source-guarded
`(rule! BODY)` to `(lambda (g) BODY)` adapter for this one body. It does not copy
or replace the shared runtime. The initial missing-prototype test errors,
wrapper failures and tied-fixture failures are all preserved and labelled
honestly. The final prototype uses the executable unequal-size domain.

## Reversals and retained limitations

The initial source, the first v3 repair and the revised pre-metadata v3 source
are retained under `checks/baseline-source/` and `checks/intermediate-source/`.
Their checks are intermediate evidence even where their old paths contain
the word “final.” Only `checks/final/` is the final generator verification set.
The last source edit corrects the palette default description; all final
required checks are rerun against the resulting exact bytes.

Self-review found useful remaining distribution restrictions: connected
shapes fit within 3×3, two neighbors occupy opposite sides of the marker,
default target colors exclude 8, and the five-pair schedule is deliberately
structured. Four-direction placement and output-distinguishing order/mask
witnesses address the reproduced shortcuts, but these finite checks do not
exclude every unlisted rule or justify model-training gains.

Both audit targets remain unchanged and actionable; `AUDIT.md` distinguishes
reproduced generated-query failures from authored-domain shortcut suspicions.
The optional repository-wide pytest run was interrupted with a failing
progress log. Its full-suite verdict and specific failure attribution remain
unknown; no passing repository-wide claim is made. Its logs and interruption
receipt remain under `checks/repository-tests/`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/23a0c42b8a1c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
