# Current notes: ed860c0a9107, v4.1.0

Review `review-c80cb054851bda44`, 2026-10-20. Generator SHA-256:
`2d7912fe3e21dbe1bc7fb9ecd3c2300aabbbca5d0a7ab5f6d29c74ba79778a18`.
Canonical Racket behavior and normalized rule hash `8e6a03efc456` are unchanged.

## Intended rule and domain

On a nonzero background, find separated equal rectangular containers. Zero is
transparent inside a container; other non-background colors are payload. Align
the containers by bounding-box coordinates and choose the first nonzero payload
in row-major object order at each output coordinate. Retain zero when none is
visible. Every generated box has a visible payload and a transparent zero.

Five exact integer controls remain: `grid_h`, `grid_w` in 14..22;
`n_containers` in 2..4; `box_h`, `box_w` in 2..5. All combinations are constructed
in separated corner slots. Explicit values override schedule defaults. Unknown
controls, invalid difficulties, non-integer scalars, booleans and invalid ranges
raise errors. Seeds are literal signed Python integers; sample indices are
literal nonnegative Python integers.

## Decisions changed in this review

- **Scalar validation.** v4.0.0 validated overrides but coerced or accepted
  malformed seed/index inputs. The baseline defect gate exposed 33 scalar
  warnings; strict scalar checks now precede random construction.
- **Connected canonical-scale payloads.** The old four-color lane scattered
  singleton cells, unlike all eight canonical records (four unique inputs).
  Its two payload colors now form connected monochrome blobs of at least two
  cells, while preserving one transparent zero per box. Other lanes retain
  multi-color variation. The detector's `marker_count` means monochrome
  singleton components here, not semantic marker objects.
- **Stronger teaching.** The previous every-grid first/last conflict did not
  distinguish column order, numerical color ranking, palette appearance order,
  numeric box ordering, or a first-container-only hypothesis. The latter was an
  exact-source prior audit lead: `review-ae7bce401b5111fe:v0001` (needs_triage).
  Default even indices now use four boxes with base colors A,B,A,B in row-major
  order. Local q=(0,0) has A,B,A,B; an adjacent p has 0,B,A,B. Protected anchors,
  zeros, and connected growth preserve these conflicts. The adjacent-cell
  orientation is sampled. These witnesses refute all seven declared rivals.
- **Lesson guarantee.** `LESSON_SCHEDULE_PERIOD = 4`, `EXAMPLES_NEEDED = 3`.
  Four consecutive default samples contain two strong even-index scenes;
  holding out any one leaves at least one in the three demonstrations. Odd
  indices retain 2..4-box variation. The four residues retain 16x16 palette
  profiles with 4,5,6 total colors and then a broader scene. Declarations and
  the lesson hook check actual rival functions rather than a separate name list.

The five-axis contract and constructive corner placement from prior review
`review-b5134cdff2f48c98` are retained. Its measurements describe v4.0.0 only;
current evidence is newly executed on the hash above. Selected authority text
was already synchronized in that prior review; this patch makes no rule edit.

## Evidence and retained counterexample

The current return retains a 12/12 green battery, 268/268 task tests, 31,590/31,590
accepted override draws over 351 cases, and 42/60 exact canonical profile hits
(easy 12/20, medium 15/20, hard 15/20). All eight canonical inputs are accepted.
The final shared Racket-labeled census materialized 300 lessons (100 per band),
1,200 unique inputs and 1,200 leave-one-out query roles: zero ambiguity against
seven unique rivals in production or rotations. Fixed-seed 0 enumeration covers
four starts in each band: 12 overlapping lessons, 48 query roles, 21 unique
inputs, again zero ambiguity. Exact seeds and source bindings are in the return's
`checks/lesson-census.json`, `checks/schedule-census.json`, and `checks/after-final/`.

`counterexamples/review-c80cb054851bda44-priority/` retains the exact old-source
seed-20000 easy four-grid lesson and public Racket receipt. Column-major,
highest-color and palette-appearance rivals fit its three demonstrations but
give 9 instead of 1 at query coordinate (1,2). Focused tests reconstruct the
geometry independently and cover all box dimensions, cyclic starts, bands,
scalar failures and explicit count overrides. `workspace/review_source.py`
reproduces the exploratory baseline probe, pinned to the old source hash.

## Proposed parametric extension

`workspace/parametric/prototype.py` selects `priority=first|last` once per episode;
`first` defaults to the exact canonical source. The alternative reverses the
object search with matching materialized Racket. Inputs do not depend on the
setting, and exported public challenges omit the setting and query labels.
Retained evidence covers 104 Racket label executions, 6 complete episodes and
24 leave-one-out roles distinguishing these two settings. Canonical records fit
both settings and are retained as an ambiguity negative control. This is a
proposed prototype, with no variant or training approval implied.

## Limits and open disposition

Corner placement remains restricted, and strong conflicts use the local origin
and one adjacent cell. The witnesses exclude a finite list of seven rivals;
they do not prove unique induction or full spatial generalization. Explicit
2- or 3-container overrides are honored but fall outside the four-box lesson
guarantee. Fixed-seed enumeration does not exhaust random seeds. The prototype
inherits these input restrictions and distinguishes only its two settings.

Proposed disposition for `review-ae7bce401b5111fe:v0001`: the first-container-only
teaching defect is addressed by the new p witness and final tests/censuses on
the exact v4.1.0 source. The maintainer must decide resolution; the protected
audit index remains unchanged. No new accepted-domain blocker was found.
Both visible-only solve records passed their three visible examples in one
actual attempt; the post-repair record discloses earlier rule exposure. Private
query correctness remains unknown pending independent scoring.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ae7bce401b5111fe:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e1094f19d9fdddc9c645c810cba5949a937c35f47c05df395b479b3a13dde462`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit resolution on2d7912fe: first_container_only is now an executable rival among7 unique competitors; protected q/p conflicts in even default four-box scenes distinguish first-container-only and6 ordering/color rivals. Any4-pair window has2 strong scenes so three demos retain one after any holdout. Reviewer268 task cases,12/12 battery,300 lessons/1200 holdouts and12 period-enumerated lessons/48 roles have0 ambiguity. Old easyseed19 indices9..12 window no longer all weak. Canonical Racket unchanged;2/3-box overrides outside guarantee, corner/origin teaching support and finite rivals remain limits; no owner rerun.

### Assessment or prior finding

## ed860c0a9107

**Reproduced teaching defect: an undeclared `first_container_only` rival survives
all three demonstrations and fails the query.**

Generator SHA-256:
`e1094f19d9fdddc9c645c810cba5949a937c35f47c05df395b479b3a13dde462`;
executed canonical rule hash: `8e6a03efc456`.

For default `difficulty="easy"`, seed 19, and sample indices 9, 10, 11, the
canonical output is exactly the first row-major container's payload with zeros
for transparency. The full selected rule and a `first_container_only` rival
therefore agree on all three demos. At sample index 12, later containers add
visible payload, so the rival and canonical query output differ. All four grids
pass `self_check`, use default generation rather than special overrides, and
were relabeled with supported canonical Racket `arcpuzzles apply`.

A bounded search over seeds 0–199 and sample indices 0–19 found 6 all-weak
three-demo windows among 3,600 easy-band windows, and none in the corresponding
medium/hard scans. This is a concrete possible shortcut, not a claim about all
production seed policies.

Evidence:

- `checks/audit/ed860c0a9107/counterexample.json` — inputs, rival outputs,
  source hashes, validator results, search denominator, and disagreement;
- `checks/audit/ed860c0a9107/racket.json` — canonical Racket outputs and executed
  rule/generator hashes;
- `checks/audit/ed860c0a9107/input.json` — exact four-grid replay batch.

No audit-target files were modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ae7bce401b5111fe-v0001/audit_assets.json), manifest SHA-256 `109403e6d992503b4ba2edb2752e27f9a1f8d2eec78c8566a5119ab81c38ecc7`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `2d7912fe3e21dbe1bc7fb9ecd3c2300aabbbca5d0a7ab5f6d29c74ba79778a18`.

# Decisions — ed860c0a9107 v4.1.0

Selected generator SHA-256: `2d7912fe3e21dbe1bc7fb9ecd3c2300aabbbca5d0a7ab5f6d29c74ba79778a18`. Baseline v4.0.0: `e1094f19d9fdddc9c645c810cba5949a937c35f47c05df395b479b3a13dde462`. The fixed canonical Racket rule remains **`8e6a03efc456`**, with authored canonical program SHA-256 `988b7333267372038ad207b59c87a6f8789ec66880ad24dd025b5bd1f0946fb6`.

## D1 — Retain the five exact controls and fixed canonical law

Keep `grid_h`/`grid_w` at 14–22, `n_containers` at 2–4, and `box_h`/`box_w` at 2–5. Explicit legal overrides take precedence over curriculum defaults and are observed from pixels. Retain the constructive separated corner layout so every advertised joint combination fits without retries. The fixed rule still extracts non-background containers, aligns their bounding boxes, and selects the first visible payload in row-major order.

This review does not reintroduce the inert palette, density, texture or placement controls removed by the prior repair. Adding those axes or replacing the packer would enlarge the change without addressing the reproduced defects. The final override gate and boundary tests verify the retained surface. [Override evidence](checks/after-final/checks/ed860c0a9107_after_override_results.json); [task tests](checks/task-tests/result.json).

## D2 — Require literal integer sampler arguments

Reject Boolean, float and string `seed`/`sample_index` values before creating the generation context; reject negative sample indexes. Continue to accept negative, zero and arbitrarily large integer seeds. The baseline accepted coercible values, and the fresh defect-lint run recorded 33 strict-scalar warnings across easy/default/hard. Silent conversion would make different requests alias unexpectedly and make schedule indexes misleading.

Focused tests cover both arguments, all five invalid scalar representatives, the negative-index case, and valid integer-seed determinism. This supplements the existing strict override validation. [Baseline defect-lint log](checks/before/checks/ed860c0a9107_before_defect_lint.log); [scalar regressions](repo/generators/ed860c0a9107/tests/test_scalar_and_morphology.py).

## D3 — Restore connected canonical payload morphology

On residue 0 of the four-sample schedule, use connected monochrome payloads with at least two cells and a protected transparent zero. Every such input has the canonical total palette size of four. Preserve this morphology for explicit two/three-container overrides as well.

The baseline structural warning was concrete: all 8 canonical records had zero monochrome singleton components, whereas seeds=indexes 1–20 in all three bands produced singletons in 60/60 inputs. Random scattered payload colors lacked that canonical morphology. The new connected lane supplies actual support instead of suppressing the diagnostic. Other residues retain richer multicolor payloads. Tests cover all 48 count/box-shape combinations at minimum canvas size, plus each difficulty band. [Source-bound structural reproduction](checks/source-review/structural-baseline.json); [morphology tests](repo/generators/ed860c0a9107/tests/test_scalar_and_morphology.py).

## D4 — Teach spatial priority and color priority with two protected coordinates

Default even-index scenes use four containers. At local `q=(0,0)`, their row-major colors are A/B/A/B; at adjacent `p`, they are 0/B/A/B. The selected rule must output A at `q` and B at `p`. This separates row-major from column-major, first from last, and object order from any fixed A/B color ranking. Because `q` is each box's first visible pixel, the numerical first-payload-color rival is also forced to disagree. A later container contributes B at `p`, excluding first-container-only.

This replaces the prior assumption that refuting last-visible adequately covered plausible shortcuts. The exact baseline seed-20000/easy lesson has three demonstrations compatible with column-major, highest-color and palette-appearance priority, followed by a conflicting query. Its four labels are publicly Racket-verified. [Question answer and exact grid](QUESTION_ANSWER.md); [Racket witness](checks/source-review/priority-witness-racket.json).

Protect first-container zero `p` without adding a second obstruction that could strand the payload in a 2×2 box. Other containers start with an adjacent q/p domino and retain a different zero. Additional colors on residue 2 are inserted outside the anchors, so the ordering evidence cannot be overwritten. Increased density alone was rejected because it would leave a nonzero chance of all demonstrations agreeing with a rival.

## D5 — Preserve a four-period curriculum and state its boundary

Declare `LESSON_SCHEDULE_PERIOD=4`. Residues 0/1/2 retain default 16×16 canvases and total palette sizes 4/5/6; residue 3 remains broad. Even residues supply the strong four-container witnesses; odd residues keep difficulty-weighted two-to-four-container diversity. Every four consecutive default draws contain two witnesses, so any single query holdout leaves a distinguishing demonstration.

Explicit two/three-container overrides remain exact. They keep valid shapes, transparency, canonical four-color morphology where scheduled, and a first-versus-last overlap, but **do not inherit the stronger seven-rival lesson guarantee**. The hook reports unresolved rivals rather than treating every lawful override lesson as automatically identifiable. Arbitrary sampling schedules and accepted-index gaps are not covered solely by the consecutive-window argument.

The shared final census checked 300 lessons/1,200 rotations on 1,200 unique inputs. The separate seed-0 period enumeration checked all four starting residues in all three bands: 12 lessons/48 rotations, with 21 unique inputs because overlapping windows reuse grids. Neither result exhausts all seeds. [Shared census](checks/lesson-census.summary.json); [schedule census](checks/schedule-census.summary.json).

## D6 — Expand the explicit rival contract and retain the audit disposition boundary

Declare seven unique semantic/lesson rivals: `last_visible`, `column_major`, `lowest_color`, `highest_color`, `palette_scan`, `numeric_box_color`, and `first_container_only`. Only the first six belong in `CANONICAL_SHORTCUTS`: they fit 8/8 canonical records; first-container-only fits 0/8. Namespace aliases yield 20 declaration bindings, not 20 independently different hypotheses. `lesson_identifiable` checks every declared lesson competitor.

Retain the existing first-container-only audit `review-ae7bce401b5111fe:v0001` as evidence about the old source. Its seed-19/easy window (demonstrations 9–11, query 12) motivated an explicit competitor and later-container contribution witness. The new construction, independent tests and source-bound census support recommending maintainer resolution as **repaired by these exact v4.1.0 bytes** after acceptance. This proposal neither auto-closes the audit nor changes approval records. [Current audit identity](repo/generators/ed860c0a9107/evidence/review_index.json); [independent teaching tests](repo/generators/ed860c0a9107/tests/test_teaching_contract.py).

## D7 — Keep first/last priority parameterization task-local and executable

Return a proposed `priority ∈ {first,last}` extension under `workspace/parametric/`, with canonical/default `first`. Both settings retain the same background cue, containers, alignment and transparency; only overlap priority changes. Optional sampled selection occurs once per episode and is reused for all demonstrations and queries. Identical input sampling across settings isolates the label change. Public challenge JSON exposes only demonstration labels and query inputs; parameters, rule text and query answers remain private.

The prototype executes materialized Racket, records source/program/body hashes, and fails closed when the expected canonical expression changes. Its final evidence contains **104 actual Racket label executions**, 8/8 canonical default matches, 8/8 alternative matches, 16 generated probes distinguishing the settings, six episodes and 24/24 identified query-role rotations. Canonical-only negative controls retain four ambiguous query-role rotations; canonical data alone does not identify priority. Four spatial rotations were relabeled independently because rotating output pixels can change priority incorrectly when row-major container order reverses.

These are checks against the prototype's two settings, not a claim that the last-priority extension excludes all seven fixed-production rivals. The extension inherits the sampler's geometry limits and remains a proposal, not a production API, approved variant or training admission. Earlier failed prerequisites/macro-adapter runs remain failed evidence; the final bounded run is the applicable result. [Prototype README](repo/generators/ed860c0a9107/workspace/parametric/README.md); [final source-bound summary](checks/parametric/final/summary.json).

## D8 — Bind completion claims to executed evidence and disclose solves

The final exact source passed **12/12 battery stages** with no advisories and **268 task test cases** with no failures, errors or skips. Racket authority checks preserve the canonical law; selected authority text is synchronized, while archival raw-code divergence remains explicitly recorded. Python mirrors support focused tests; they do not replace Racket label authority. The exploratory baseline 300-lesson mirror probe and final public census use different sampling recipes, so their counts are not paired causal rates. [Final battery](checks/after-final/checks/ed860c0a9107_after_battery_summary.json); [task-test receipt](checks/task-tests/result.json).

The blind pre-repair solve concerned separate task `3f5263211041`, disclosed no earlier exposure and passed 3/3 visible examples in one real attempt. The post-repair `ed860c0a9107` solve disclosed earlier rule exposure, did not consult references during the solve subphase, and also passed 3/3 visible examples on its first attempt. Both masked-query outcomes remain unknown pending independent scoring; neither solve is admitted to training by this return. [Blind solve summary](solve-blind/summary.json); [post-repair summary](solve/summary.json).

Remaining limits: corner-only placements, fixed-origin/adjacent strongest anchors, explicit two/three-container lessons outside the expanded guarantee, finite declared-rival coverage, bounded prototype seeds, and unmeasured downstream model effects. Expanding arbitrary placement or adversary families would need separate constructive design and evidence. No claim of universal unique induction is made.
