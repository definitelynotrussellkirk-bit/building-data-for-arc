# Working notes: 784b131b3b93

## Current selected design

Rule hash `4b6cdc515f3f`: split an even-width input into equal horizontal
halves; output 5 exactly where both aligned cells are zero, otherwise 0.
Generator version `2.0.0`, final source SHA-256
`d4734df9e5d31cf0c76dd4c8bfa44d254079baf0331baf80d889a7203158e3ac`.

Normal draws explicitly contain all four aligned occupancy states `00`, `10`,
`01`, and `11`. Each half uses background 0 plus one distinct nonzero color;
color 5 is output-only. Exact public controls are `grid_h` 3..14, `half_w` 3..7,
left/right colors, `both_zero_target` 1..6, and six observable panel patterns.
Unknown keys, scalar coercions, invalid calls, and incompatible equal-color
requests fail loudly. Diagnostic degenerate textures execute but are rejected
by the teaching grammar.

## Reversed decisions

The prior density-first flow treated `both_zero_target` as a lower bound and
then mutated evidence, so a request for one could realize eight. It was replaced
with explicit state allocation: evidence is intrinsic and the target is exact.
The old symbolic range `1..h*half_w` was replaced with the probeable selected
curriculum range 1..6. A focused regression retains the seed-0/sample-0 witness.

The prior generator lacked observable exact-axis provenance, a canonical rule
pin, and an executable lesson contract. It now exposes `observe_overrides`, pins
`RULE_HASH`, declares truth-table witnesses/rivals, and requires three correct
demonstrations.

## Evidence

After battery: 12/12 green. Portable selected-task tests: 70 passed. Override
matrix: 78,840 draws, 876 cases, zero findings. Profile floor: 32/60 exact
4×14×3 hits with support in every band. Lesson census: 300 lessons, 1,200 pairs
and 1,200 query rotations, zero ambiguity/errors against seven declared rivals.
See `WORK/REVIEW.md` and `WORK/checks/` for source-bound receipts.

The selected authority changed only in `racket_target.target_code`, which now
matches canonical modern Racket; archival `raw_code` and rule semantics were
preserved.

## Proposed extension and limits

`workspace/parametric/` contains an unapproved episode-level
`positive_state ∈ {both_zero, both_nonzero}` prototype. It is separate from the
selected path and has finite two-seed evidence only.

Known limits: the normal sampler intentionally does not cover every lawful
multicolor input or every possible both-zero count; lesson evidence covers a
finite declared rival set and finite seeds. No training approval is granted by
this review. No repair blocker remains.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-75f0e94a3e3807b9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2048696ff313f40630b6f0b2b401859a7aa3dc3a93e6e1cef9909652d36fa2e6`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused closure against current d4734df9e5d31cf0c76dd4c8bfa44d254079baf0331baf80d889a7203158e3ac. Owner static inspection confirms _build_scene selects exactlycells[:both_zero_target] thenassignsremainingoccupancystates;numeric1..6targetbound,observe_overrides state00count,strictunknown/scalarrefusal. Focusedtest_both_zero_target_is_an_exact_observable_contract_regression requests1 andassertsrealized1. Reviewer70tests/freshfullpacketreplay and77940acceptedoverridechecks with900declaredincompatibilities closeprior lower-bound-not-exacttarget andmissingobserver/unknown-keyfindings. Moderncanonicaltargetcopyseparatelybound;noowner runtime rerun.

### Assessment or prior finding

## 784b131b3b93

**Classification: Reproduced defect; audit-only target left unchanged.**

Assigned generator SHA-256 `2048696ff313f40630b6f0b2b401859a7aa3dc3a93e6e1cef9909652d36fa2e6`; canonical rule hash `4b6cdc515f3f`.

The override checker fails fast before generation because `both_zero_target` declares the symbolic range `1..h*half_w`, which the matrix cannot parse, and because exact semantic axes `half_w`, `left_color`, and `right_color` lack `observe_overrides`. It also warns that unknown override keys are accepted. Evidence: `checks/audit/784b131b3b93-override-run/checks/784b131b3b93_before_override_results.json`.

The unprobed target axis has a concrete semantic failure. With easy seed 0, sample 0, a 3×3 pair of zero-density panels, and `both_zero_target=1`, generation returns a lawful 3×6 input containing **8** aligned both-zero pairs. `_ensure_both_zero` treats the requested value as a lower bound, and the subsequent forced-evidence rewrite can alter it again. `self_check` returns `[]`; the input **passes the current validator and belongs to the documented generated domain**, but the accepted exact override is not realized. The canonical Racket output has eight color-5 cells, matching the observed eight both-zero pairs. Evidence: `checks/audit/784b131b3b93-counterexample/audit-evidence.json`, with raw apply receipt at `checks/audit/784b131b3b93-counterexample/racket-output.json`.

Likely repair: define an observable exact count contract, perform evidence placement before exact-count adjustment, and make `_ensure_both_zero` both add and remove pairs until the target is exact—or rename the axis to a minimum and declare it diagnostic. No source was modified because this was a findings-only audit.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-75f0e94a3e3807b9-v0001/audit_assets.json), manifest SHA-256 `1b84330520ad4679fd4a5b97131d22cd307b69d53d5b2b8dea7cbebb1af7eedf`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `d4734df9e5d31cf0c76dd4c8bfa44d254079baf0331baf80d889a7203158e3ac`.

# Decisions for `784b131b3b93`

## D1 — Treat `both_zero_target` as an exact, bounded contract

**Prior choice.** The baseline advertised `1..h*half_w`, but its helper enforced
only a lower bound and later evidence mutations could change the count again.
The original rationale is unknown.

**Alternatives considered.** Rename the axis to `min_both_zero`; keep the
symbolic range and mark it diagnostic; or implement exact realization over the
entire area-dependent range.

**Decision.** Keep the useful name, make it exact, and bound the advertised
normal curriculum to 1..6. The generator can realize each value in every band,
and `observe_overrides` reads the exact realized count from the grid.

**Probe/evidence.** The old seed-0/sample-0 request for one produced eight. The
new regression requires one; the final override matrix reports zero findings in
78,840 draws.

**Limit.** Canonical rule semantics allow more than six positives on larger
grids; such counts are outside this selected normal sampler's advertised axis,
not invalid rule inputs.

## D2 — Build from the four aligned occupancy states

**Prior choice.** Draw two panels by density, then patch in a positive and
negative witness. This made exact counts fragile and did not guarantee all
semantic branches.

**Alternatives considered.** Continue post-processing the density grids until
counts converge, or generate left/right panels independently and reject draws
that lack states.

**Decision.** Allocate `00`, `10`, `01`, and `11` directly, with at least one of
each and exactly the requested number of `00` cells. This makes the NOR truth
table explicit and eliminates unbounded rejection/post-mutation logic.

**Failure modes checked.** Smallest 3×3 aligned area, target 1, target 6, every
difficulty, every panel pattern, and conflicting colors.

## D3 — Make every advertised exact control observable

**Prior choice.** Exact-looking controls had no `observe_overrides`; unknown
keys were accepted, and the symbolic target range could not be probed.

**Alternatives considered.** Downgrade layout to diagnostic provenance or
remove the pattern axis.

**Decision.** Keep six patterns but encode each with a unique permutation of
the first three non-`00` states. This lets the checker recover the selected
pattern from the grid, just as it recovers dimensions, colors, and target count.
Unknown keys and scalar coercions now fail loudly.

**Limit.** The signature is a generation-control marker, not part of the ARC
rule. It may be unsuitable for a future curriculum that wants completely
naturalistic layout statistics.

## D4 — Preserve distribution breadth while guaranteeing canonical support

**Prior choice.** Difficulty-dependent random sizes happened to miss or weakly
support the only canonical profile, 4×14 with three input colors.

**Alternatives considered.** Emit only canonical dimensions; use rejection
sampling; or add an explicit hidden probability draw.

**Decision.** Fully default even sample indices use a deterministic 4×7-half
anchor; odd indices use difficulty-dependent ranges. This avoids hidden random
provenance and preserves broad sizes. Exact size overrides always win.

**Evidence.** 32/60 exact hits, with 9/20 easy, 12/20 medium, and 11/20 hard.

## D5 — Use one distinct foreground color per half, excluding output color 5

**Prior choice.** The baseline allowed broader density/palette effects but did
not enforce a clean semantic color role. Original rationale is unknown.

**Alternatives considered.** Permit multiple colors per half or equal left/right
colors.

**Decision.** Each half uses background 0 plus one foreground; foregrounds are
distinct and neither is 5. This preserves the occupancy rule while preventing
output-color leakage and color-equality shortcuts.

**Limit.** This is a deliberately clean teaching grammar. The canonical rule
would also operate on multicolor panels; that broader domain is not sampled.

## D6 — Keep negative fixtures, but outside the teaching grammar

`no_both_zero`, `all_both_zero`, and `same_halves` remain runnable diagnostic
fixtures. They execute the rule but `self_check` rejects them because they omit
semantic branches or collapse panel roles. Combining them with count/pattern
controls is rejected rather than silently producing an ambiguous contract.

## D7 — Three demonstrations; production and arbitrary retained query rotations

The lesson contract requires at least three correct demonstrations. Every normal
example already contains all four occupancy states, so one would distinguish
the seven declared truth tables, but retaining three matches the task's normal
curriculum and gives redundancy. The production sampler uses three demos and
one query; the census held out every one of the four materialized pairs in turn.
Both ordered production and all retained rotations passed for 300 lessons.

**Limit.** The census does not enumerate every seed or every conceivable rival.

## D8 — Synchronize only selected `target_code`

The canonical and legacy Racket programs were semantically equivalent, but the
authority-sync gate requires the selected target to match canonical authority.
I preserved `raw_code` as archival evidence and replaced only
`racket_target.target_code` with the exact canonical modern program. No semantic
rule change or canonical-ledger edit was made.

## D9 — Keep `positive_state` as a separate proposal

A bounded episode-level parameter between `both_zero` and `both_nonzero` is
useful because it changes one Boolean predicate while preserving the input
domain and output vocabulary. It is selected once per episode, and every demo
refutes the rival setting. The prototype is isolated under
`workspace/parametric/`; it is not wired into `generator.py`, catalog approval,
or production lesson assembly.

Rejected parameter ideas included changing output color or half orientation:
those would entangle semantic roles with surface transformations and offer less
controlled evidence about rule induction.

## D10 — Prior evidence use

The retained audit from `review-75f0e94a3e3807b9:v0001` was used as a lead only.
All repair claims here are based on the selected baseline and newly retained
before/TDD/after evidence. The two newly assigned audit targets were likewise
reproduced on their assigned hashes and left unchanged.
