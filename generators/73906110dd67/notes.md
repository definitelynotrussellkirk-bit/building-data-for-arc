# Working notes: 73906110dd67

## Scope and prior evidence

Assignment `review-e3e0efe8616db5e1` repaired pinned generator SHA-256
`d7ebd5d5c58838cfeeb9d676c0d70f83c53a3bc58ee69077d1fd691547e1c1a5`
(version `3.0.0`). The unverified prior return `review-ae5b6cb7976aeac1:v0002`
was used only as a lead: it reported a clean finite contract review. Retained
notes `GNOTE-002892` (compact fixed-slot layout) and `GNOTE-002889` (four-profile
schedule) identified the two areas remeasured here. All final claims below come
from the pinned packet and newly retained checks.

The canonical Racket authority was already correct and remained byte-for-byte
unchanged. `RULE_HASH = "9b7f117d5438"` stays pinned.

## Baseline findings

The official before battery was 12/12 green, but source-bound probes exposed
three distribution gaps not represented by those gates:

1. The placement algorithm always used exactly two origin rows and two origin
   columns. Across the exhaustive accepted matrix, all 17,496 generated scenes
   had that two-by-two lattice signature.
2. Heights 8 and 9 were rejected even though the canonical task contains 8x11
   and 9x10 inputs. The reusable matrix recorded 3,888 failures among 21,384
   requested cases and only 81 of the 99 advertised/canonical canvas sizes.
3. Gray (`5`) was absent from generated palettes. The accepted matrix reached
   colors 1,2,3,4,6,7,8,9 but not 5.

A first repair (version `4.0.0`) fixed those distribution gaps and passed the
12-stage battery, but the required 300-lesson census exposed a teaching defect:
239/1,500 rotated hold-outs were ambiguous. `largest_three_only` survived 225
rotations and `bbox_area_desc` survived 14 because each decisive witness occurred
in only one schedule profile.

## Final repair in version 4.1.0

- Accept exact `grid_h` values 8..18 and cycle scheduled canonical profiles
  through 8x11, 9x10, and 10x10.
- Replace fixed corner slots with cached staggered left/right row schedules.
  A full blank divider separates lanes; repeated objects in one lane have a
  blank-row moat; lexicographic inequalities preserve requested row-major order.
- Vary the divider and per-object columns independently. Final exhaustive draws
  use origin rows and columns 0..17, with three or four distinct origin rows.
- Sample the complete foreground palette 1..9 while keeping low/high/mixed
  palette classes structurally observable.
- Make both canonical profiles width two. Make both generalized profiles
  four-object, width-three, spread-size bounding-box conflicts. Thus any four
  pairs remaining after a five-pair hold-out include both a width-two witness
  and a four-object/bounding-box-conflict witness.
- Add regressions for every canonical canvas size, exact height-8 overrides,
  non-lattice row support, full palette support, all five-pair query rotations,
  and the reusable distribution probe.

## Final evidence

- Generator SHA-256:
  `e42e0baab3290309a58f6864e4d1fb91c6f1271f89bd79175ed1d94b3c68661d`.
- Official after battery: 12/12 green. Override stage accepted 38,790/38,790
  draws across 431 cases and three bands.
- Semantic gate: 290/600 strict, 4/4 canonical inputs accepted, 7/7 witnesses,
  7/7 rival claims, 12/12 production lessons, and 0/60 ambiguous rotations.
- Final task-local portable suite: 24 passed.
- Full lesson census: 300 lessons, 1,500 pairs, 1,500 unique inputs, 1,500 query
  rotations, zero ambiguities, materialization errors, hook warnings, or scoring
  errors.
- Exhaustive task-local probe: 21,384 joint override cases, zero failures, all
  99 canvas sizes, all colors 1..9, 20,834 origin patterns, 21,384 unique inputs,
  and zero ambiguities in 180 cyclic hold-outs.

## Deliberate limits

The object vocabulary remains finite: component areas come from two small size
families and crops fit within 4x3. Layouts use two separated lanes, although
origins vary broadly and objects occupy three or four distinct rows/columns in
most draws. Declared-rival and finite census success does not prove unique
induction against every undeclared rule or every lawful input. The Python mirror
supports diagnostics; Racket remains label authority.
## Current reviewer considerations

Source SHA-256: `e42e0baab3290309a58f6864e4d1fb91c6f1271f89bd79175ed1d94b3c68661d`.

# Decisions for `73906110dd67`

All final implementation choices below are bound to generator SHA-256 `e42e0baab3290309a58f6864e4d1fb91c6f1271f89bd79175ed1d94b3c68661d`. “Original rationale unknown” means the pinned source did not record why version 3.0.0 made that choice; any likely motivation is explicitly marked as inference.

## D1 / R1 — canvas controls and canonical dimensions

**Input choice.** Declare and honor exact `grid_h=8..18` and `grid_w=10..18`; schedule canonical-like profiles through 8×11, 9×10, and 10×10.

**Original rationale.** Unknown. Version 3.0.0 accepted heights only 10..18, plausibly to simplify packing, but that inference conflicted with the actual 8×11 and 9×10 canonical inputs.

**Alternatives considered.** Keep 10..18 and remove the canonical-size claim; special-case only 8×11 and 9×10; or support the complete rectangular envelope. The complete envelope was chosen because it makes the declared integer controls literal and is cheap to exhaust.

**Probe and result.** `checks/distribution/comparison.json` requested all 21,384 joint cases. Baseline rejected 3,888 and covered 81 dimensions; final accepted all cases and covered all 99 dimensions. Task tests separately pin every canonical canvas size and an exact height-8 override.

**Failure modes and limits.** Exact dimensions do not imply uniform sampling of every dimension under defaults. Packing remains constrained by the finite shape and two-lane grammar.

## D2 / R1 — staggered two-lane placement

**Input choice.** Replace the fixed corner-slot lattice with cached, shape-aware left/right placements separated by a blank vertical divider. Same-lane objects have a blank-row moat, and schedules are filtered so object origins preserve the requested row-major size order.

**Original rationale.** Unknown. The old 2×2 slot lattice likely made non-touching and scan order easy to guarantee, but every accepted exhaustive draw then had exactly two origin rows and two origin columns.

**Alternatives considered.** Fully rejection-sampled free placement; random translation of the old lattice; or deterministic precomputed feasible schedules. Random translation would preserve the two-by-two signature, and free rejection sampling complicates exact control/determinism on 8-row canvases. Cached feasible schedules were chosen for totality, deterministic freshness, and broad support.

**Probe and result.** The final matrix reaches origin rows and columns 0..17, uses three or four origin rows, and produces 20,834 distinct origin patterns in 21,384 cases. `self_check`, exact override observation, and uniqueness all pass.

**Failure modes and limits.** The divider still creates two semantic lanes; this is a deliberate residual restriction. The probe measures support, not a statistical claim of uniformity.

## D3 / R1 — full foreground palette

**Input choice.** Allow every non-background ARC color 1..9, including gray 5, while preserving observable `low`, `high`, and `mixed` palette classes.

**Original rationale.** Unknown. Version 3.0.0 omitted 5, perhaps to reserve gray by convention, but the task rule is color-agnostic and no frame/background role uses 5.

**Alternatives considered.** Preserve the omission; add 5 only to `mixed`; or cover 1..9 across the declared classes. Full support was chosen because color has no semantic role and the linter/probe can verify it directly.

**Probe and result.** Baseline support was eight colors; final support is exactly 1..9 across the exhaustive matrix. A task regression fails if any foreground color is absent.

**Failure modes and limits.** Distinct colors are still required within one grid, so a single example does not contain all nine colors.

## D4 / R2 — redundant four-profile teaching schedule

**Input choice.** Keep four deterministic schedule profiles. Profiles 0 and 1 are canonical-like, three-object, width-two cases. Profiles 2 and 3 are four-object, width-three, spread-size cases with an occupied-area-versus-bounding-box-area conflict.

**Original rationale.** The pinned generator already used a four-profile cycle, but only one profile supplied each decisive witness. The reason for that nonredundancy was not recorded.

**Alternatives considered.** Treat rotations as diagnostic and retain 4.0.0; add a fifth profile; make all profiles four-object; or duplicate the two decisive properties across the two generalized profiles. Retaining 4.0.0 was rejected after 239/1,500 strict rotation failures. A fifth profile adds curriculum length, and making every profile generalized weakens canonical resemblance and the fixed-width counterexample. Redundant generalized profiles were the smallest repair.

**Probe and result.** `checks/lesson-census-v4.0-ambiguous.json` is the retained failing experiment. `checks/lesson-census.json` tests 300 five-pair lessons and all 1,500 hold-outs with zero ambiguity. The task regression checks every query position in deterministic five-pair windows.

**Failure modes and limits.** The proof is against the generator's declared finite rival set, not all possible programs. Consecutive five-pair lessons are the tested assembly policy; arbitrary nonconsecutive curricula were not claimed.

## D5 — shape and size vocabulary

**Input choice.** Retain small 4-connected crops fitting within 4×3 and two size families (`consecutive`, `spread`), including deliberately sparse 3×3 shapes paired with a larger 4×2 object to reverse bounding-box and occupied-cell ordering.

**Original rationale.** The compact vocabulary already supported canonical-like objects and reliable small-canvas packing. This was retained rather than broadening shape generation and placement simultaneously.

**Alternatives considered.** Procedurally enumerate all polyominoes, increase maximum box size, or leave the vocabulary unchanged while improving layout/schedule coverage. The last option was chosen to isolate the measured defects and keep Racket-label semantics straightforward.

**Probe and result.** All exact control combinations pass; the witness at `checks/shortcut/73906110dd67/input.json` has occupied areas 8, 6, 4, 2 while the first two bounding-box areas are 8 and 9, forcing the intended/rival disagreement.

**Failure modes and limits.** This remains a finite object vocabulary and can induce a shape prior. That is the main documented residual distribution limitation.

## D6 — authority boundary

**Input choice.** Leave the canonical Racket rule and canonical puzzle data unchanged; keep the Python mirror for diagnostics and task-local rival checks only.

**Original rationale.** The authority already correctly extracted components, cropped them, sorted by occupied cell count, and stacked them with gaps. The defects were in generation and curriculum, not labels.

**Alternatives considered.** Edit the Racket rule to match an easier generator or change canonical data. Both were rejected because the source-bound Racket applications already matched the intended rule and rule hash `9b7f117d5438`.

**Probe and result.** The final battery's rule smoke and authority-sync stages are green. `checks/shortcut/73906110dd67/racket.json` records executed and catalog rule hashes matching and agrees with the Python intended output.

**Failure modes and limits.** Python diagnostic agreement is not promoted to authority; Racket remains the label source.

## D7 — reusable distribution probe

**Input choice.** Add `workspace/distribution_probe.py` and test it as a task-local tool.

**Original rationale.** The shared 12-stage battery was green both before the distribution repair and for the rotation-ambiguous intermediate repair, so future agents needed a source-bound probe that measures the exact omissions found here.

**Alternatives considered.** Keep one-off notebooks/logs, add every task-specific condition to production code, or create a reusable task-local CLI. The CLI was chosen because it can load a historical generator file, derives rivals from the generator declarations, emits compact JSON, and runs independently of private runner internals.

**Probe and result.** The final task test invokes the CLI and checks its rotated-lesson output. `checks/distribution/comparison.json` is a compact before/after product of the tool.

**Failure modes and limits.** High-volume checks use the independent Python mirror and therefore supplement rather than replace Racket authority checks. The full joint matrix is specific to this task's axes.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1c053cf4807c3145:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e42e0baab3290309a58f6864e4d1fb91c6f1271f89bd79175ed1d94b3c68661d`. At disposition, audited bytes match the current source.

### Current decision

Reported12 tests,864 override combinations and180 rotations clean on e42e source. Prior clean assessment on d7eb source remains a different source identity. Bounded reviewer-reported assessment only; other findings/source versions unchanged. Evidence=/home/user/Desktop/ARCpuzzles/var/review/new-return-tools-review/tool-disposition-proposals-nine.json sha256=76a7ea73fa5513ccc75ba5c5d6aad9abc549b59dfa65563ac320261676fd2870

### Assessment or prior finding

## 73906110dd67

**Conclusion: No issue found.** Source SHA-256
`e42e0baab3290309a58f6864e4d1fb91c6f1271f89bd79175ed1d94b3c68661d`,
rule hash `9b7f117d5438`.

I checked the task's canonical acceptance, exact override behavior, named
scan-order/color-order/bbox-area/alignment/gap/fixed-width/fixed-cardinality
rivals, and five-pair query rotations. The combined audit ran all 12 portable
task tests successfully and the strict semantic gate passed:
`checks/audit/73906110dd67/combined/result.json`.

I also ran the retained task-local distribution probe on both boundary heights
and widths while exhausting every other advertised axis. It covered 864 exact
override combinations with zero errors, all foreground colors 1..9, 860 distinct
origin patterns, and 180 held-out query rotations with zero named ambiguity:
`checks/audit/73906110dd67/distribution_probe_quick.json`.

The finite rival set is not a universal induction proof, but I did not find a
concrete validator-accepted counterexample, dead control, or surviving declared
shortcut in the checked domain.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## 2026-10-25 native parametric reviewer build

- Kept production generator `4.1.0` and its canonical rule unchanged. The exact
  default program is bound at SHA-256
  `35232ccc72f09e238bf3899568fe43620b607d124cc5ea71394181fb0d81f7b6`.
- Added `order_metric = cell_area | bbox_area`. Step A extracts all objects,
  measures both occupied and bounding-box area, and orders their tight crops;
  step B stacks that ordered sequence with one blank separator row.
- The fixed scene grammar contains areas/bounding boxes `8/8`, `5/9`, `6/6`,
  and `3/3`, so the two settings disagree on matched inputs. Minimum two-example
  lessons reject the other setting plus scan-order, smallest-first, color-order,
  no-gap, center-alignment, and reversed-order shortcuts.
- Retained source-bound evidence: 18/18 task tests, 72 protected-Racket audit
  evaluations, 256 prefix-stability episodes (2,560 pairs), authoring preflight,
  protected causal replay, and 16 verified one-query public views with 24
  private-field invariance checks.
- The fourth query is a substantive 30x30 case. Demonstrations are independently
  selectable from 2 through 6; all settings share identical inputs and four
  prefix-stable queries.
- Limit: the rival audit is finite and does not prove unique induction against
  every undeclared program. Reviewer work is ready; owner exact-source native
  qualification and fresh acceptance remain the next required action.
