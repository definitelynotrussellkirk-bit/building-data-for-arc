# Current decisions: 2a1d414bfe10

Version 3.0.0 samples inputs for the unchanged canonical rule: extract fixed
colors 1, 2 and 3, translate each support independently to its own bounding-box
origin, retain coordinates belonging to exactly two supports, crop that set,
and paint it 8 on background 0. Racket remains the label authority.
`RULE_HASH = 95b31785aa4f`. The selected bank's `racket_target.target_code` was
synchronized to canonical program text; only comment/text divergence was removed.
No canonical ledger or reference behavior changed.

## Selected distribution

- Each color is one connected shape. Each pair of bounding boxes has at least
  one background row or column between them. Boxes can interleave globally;
  a complete blank line need not divide the whole scene.
- Exact controls are only `grid_h` in 8..16 and `grid_w` in 10..18. Every joint
  combination is supported in every band. Unknown controls and invalid values
  raise; `None` means no override. Fixed semantic colors are not palette knobs.
- Even indices use compact five-cell shapes grown in independent 2x3, 3x2 or
  3x3 frames. Compact grid sizes favor canonical sizes in every band, including hard.
- Odd indices use broader connected shapes, at most 5x5 and 5..9 cells in easy
  or 5..12 otherwise. Accept a broad draw only when the intended output differs
  from every declared rival. All returned grids have a nonempty exact-two set.
- Construction retries whole shape triples before painting, at most 4096 times.
  Exhaustion raises. A feasible initial packing is relocated by three passes
  of whole-box moves. No partial grid is a fallback.

## Teaching policy and limits

`EXAMPLES_NEEDED = 3`, schedule period 2. Four consecutive same-seed samples
contain two broad witnesses. With three demonstrations and one query, each
single-pair query rotation leaves a broad witness in the demonstrations.
This argument concerns consecutive accepted samples and seven declared rivals.
Production can skip rejected draws: inspect its accepted indices before applying
the argument to materialized lessons.

Rivals: `clip_3x3`, `first_five`, `at_least_two`, `odd_parity`, `pair_12`,
`common_bbox`, `uncropped`. Only the first two fit all five canonical pairs and
are declared canonical shortcuts. `common_bbox` fits four of five. Python
incidence calculations select witnesses; Racket still produces saved labels.

Final evidence: `checks/lesson-census-final.json` has 300 production lessons,
1,200 unique inputs and 1,200 rotations with no reported ambiguity/error; accepted
indices were consecutive and there were no materializer rejections. The fixed
seed-17 census enumerates both period-2 starts in each band: six overlapping
lessons, 24 rotations, seven unique inputs. Finite rival checks do not establish
unique induction against undeclared hypotheses or unrestricted lesson assembly.

The sampler intentionally covers a subset of the reference domain: connected
separated shapes, bounded sizes and nonempty output. It does not generate missing
colors, empty exact-two sets, every polyomino or every lawful packing. Relocation
is not uniform over legal packings. `strict_canonical_like` checks this connected-
shape domain; its 100% pass rate is not complete distribution coverage.

## Repairs and reversals

R1: The old placement predicate ignored an occupied target cell; easy seed 205,
index 0 lost every color-1 cell. Forced placement failure returned a partial empty
grid. Constructive complete placement replaces both behaviors. See
`counterexamples/placement_overwrite.json` and `checks/baseline-probe/`.

R2/R3: Shared full frames, disconnected supports, ineffective size controls and
a missing teaching contract were replaced by the choices above. Independent
connected shapes reflect all five canonical inputs; broader witnesses challenge
five-cell/3x3 shortcuts. Original intent beyond the prior summary is unknown.

R4: The intermediate repair guaranteed packing with a global blank cross. Review
showed that it excluded canonical interleaved layouts. The final version relocates
complete boxes after obtaining a feasible start. Two layout regressions failed
before this change and pass afterward. Independent review checked 776 cases:
normalized supports and intended outputs were unchanged, with no geometry failures.
See `counterexamples/interleaved_layouts.json` and `checks/code-review/`.

No unresolved main-task blocker was found in the tested scope. Separate audit
findings concern unchanged audit sources; this repair does not resolve or approve
those tasks. Training admission remains a maintainer action.
## Current reviewer considerations

Source SHA-256: `20511c0246309caa09824dd6db6d79ade9715beec22ffaab05047ef66f234695`.

# Distribution and repair decisions

Assignment `review-59ef52d435287a30`; task `2a1d414bfe10`; version 3.0.0.
Final generator SHA-256:
`20511c0246309caa09824dd6db6d79ade9715beec22ffaab05047ef66f234695`.

## R1 — Construct complete placements

The original `_free` predicate examined neighbors but skipped the occupied cell
being tested. A one-cell occupied grid reproduces the predicate defect. Ordinary
seed 205/easy/index 0 overwrote all color-1 cells; seed 482/default/index 0 produced
damaged supports with empty exact-two output while passing the old validator.
The reference can execute these inputs; successful execution alone does not
certify the generator's input contract. Evidence: `checks/baseline-probe/REPORT.md`,
its public Racket receipts, and the selected task's `counterexamples/placement_overwrite.json`.

The repair constructs all shapes before painting and starts with a feasible
three-slot packing. Invalid triples are retried as whole units. The 4,096-attempt
bound raises on exhaustion; it never returns an unfinished grid. Unbounded random
placement retries were rejected because their tail can create hidden timeout or
sampling biases. The forced-failure regression is explicitly fault injection,
not a measured ordinary failure rate.

## R2 — Expose effective exact controls and validate pixels

The old size axes did not control the resulting pixels, and palette/texture axes
had no useful rule-preserving effect. The selected interface exposes height 8..16
and width 10..18; all 81 joint combinations are feasible in every band and phase.
Values must be proper integers. Unknown keys and difficulties raise; `None` means
no override. The observer recovers dimensions from the returned grid. Colors
1/2/3, background 0 and output 8 are fixed by the task; arbitrary palette changes
would change semantic roles.

Validation now checks actual rectangular grids, proper integer colors, presence
and connectivity of every shape, separated boxes and a nonempty exact-two set.
Metadata cannot bypass it. All five canonical inputs pass. This broad domain
validator is not a measurement of how completely the sampler covers that domain.

## R3 — Independent connected shapes and teaching witnesses

The original summary states that every shape spanned a shared full frame to keep
independent normalization aligned. That choice made independent bounding-box
geometry almost absent; the few measured unequal boxes were damaged placements.
At seeds 0..499/index 0, disconnected supports occurred in 483/500 easy, 496/500
default and 497/500 hard draws. All five canonical inputs have connected five-cell
shapes with unequal individual boxes. Connectivity is a canonical-domain choice,
not a newly asserted limitation of the Racket program. Other original author
intentions are unknown. See `checks/baseline-probe/REPORT.md`.

The new sampler grows each connected support in its own frame. Reproducing only
canonical five-cell/3x3 shapes would leave two shortcuts unchallenged: truncating
each shape to its first five sorted cells, or clipping normalized supports to 3x3.
Both match 5/5 canonical outputs. We retain compact examples and add broader
supports that distinguish these shortcuts. Canonical fit is checked independently
in `checks/lesson-census-final.json`.

Even indices are compact: five cells per shape, independent 2x3/3x2/3x3 frames.
Odd indices are broad: supports up to 5x5, 5..9 cells in easy and 5..12 otherwise.
Each broad example must disagree with all seven declared rivals: `clip_3x3`,
`first_five`, `at_least_two`, `odd_parity`, `pair_12`, `common_bbox`, `uncropped`.
The common-box rival fits only 4/5 canonical pairs, so it is an ordinary competitor,
not a declared canonical-fitting shortcut. Python calculations select witnesses;
all exported labels still come from Racket.

Every band's compact dimension distribution favors heights 9/10 and widths
11/12/13 while retaining the full exact-control domain. Hard favors larger broad
grids but retains compact examples. Final profile-floor exact counts are 6/20
easy, 8/20 medium and 4/20 hard; before counts were 6/20, 2/20, 0/20. This restores
ordinary hard-band canonical-size support. Evidence: the before and final
`2a1d414bfe10_*_profile_floor.json` reports.

## Lesson assembly policy and measured scope

Use three demonstrations and one query from consecutive accepted samples at the
same seed. Profile period is two. Any four consecutive samples have two broad
examples, so holding out any single pair leaves a broad demonstration refuting
the seven named rivals. `lesson_identifiable` checks actual demo/query labels:
a rival is ambiguous only if it fits every demo and disagrees on the query.
This finite rival contract cannot establish that no other hypothesis exists.

Production materialization can advance indices after rejecting draws. The final
300-lesson census uses the production sampler, 100 requested starts per band
(0..99), with deterministic task/band/index-derived seeds. Accepted-index records
show no skips or rejections. All 300 lessons materialized: 1,200 pairs, 1,200 unique
input hashes, and 1,200 rotations; zero ambiguity, scoring errors or hook warnings.
Racket supplies all census labels. See `checks/lesson-census-final.json` and
`checks/census-summary-final.json` for exact seeds and denominators.

The fixed-seed-17 census enumerates starts 0 and 1 in each band, covering the
complete declared period. It has six overlapping lessons, 24 pair appearances and
24 rotations, but only seven unique inputs. Both production and rotation verdicts
report no ambiguity. The runtime's generic `period: 6` residue-summary field is
not the generator's declared schedule period; the actual enumerated start count
is two. Evidence: `checks/schedule-census-final.json`.

Arbitrary demo counts, independently shuffled examples, skipped-index curricula
and undeclared rivals remain outside this claim. The solve uses three demos and
two masked queries; its own declared-hook result is reported separately. A visible
solve pass is not hidden-query or training-performance evidence.

## R4 — Remove the intermediate layout restriction

The first repair used quadrants separated by a global blank cross. It passed all
twelve checks, yet canonical shapes can interleave without a complete internal
blank line. Two layout regressions failed against intermediate SHA
`9630ed979d532d0fbc2c62188dae76ab73fb61fd9a473ebc3f8d419295e99b12`.
That source and red/green evidence remain under `checks/layout-repair/`.

The selected version starts from feasible boxes, then makes three shuffled passes
of whole-box relocation. Each move chooses a legal origin relative to the other
boxes; the current origin always remains a candidate. Independent review checked
776 tuples across all dimensions, four difficulty values, both phases and
minimum-size stress cases. Normalized supports and dense-oracle outputs were
preserved in every case, with no geometry failures. Four concrete interleaving
witnesses are retained in the selected task's counterexamples.

This is not uniform sampling of all legal packings, nor proof of complete layout
support. Hard-coded canonical placement templates were rejected because they
would replace a coverage gap with memorized geometry. The selected relocation
method supplies observed support for the missing features without changing labels.

## Authority and residual limitations

Canonical ledger SHA remains
`a1af567baabfe06f90d62dac826fa51e4d50bf322e6712cbaf6bc6aabc4a757b`.
Only the selected bank's `racket_target.target_code` was synchronized to canonical
text, removing active comment-only divergence. Final authority checks report exact
agreement and execution parity. Executed callable SHA:
`003f0470484a2902d778b6fb439a478f1e93b365c9c64955e892816a2362da8f`.

Missing-color, empty-output, disconnected-shape and arbitrary-size distributions
are not claimed. Broad witness rejection and compact/broad alternation impose
deliberate biases. The optional support probe measures selected marginal features,
not joint support or frequencies. No Qwen training experiment, token-level model
trace, training admission or universal induction claim is part of this return.
