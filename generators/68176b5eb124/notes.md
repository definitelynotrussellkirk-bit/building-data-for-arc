# Current decisions: 68176b5eb124

## Rule and teaching domain

The pinned canonical Racket rule (`2dc205754ece`, full rule-text SHA-256
`77801865bb5dbba8ad9b7d10ec58bcf340178163b5eacb04ec8dd8e83691a98d`)
reads the original grid and fills an interior zero cell exactly when all four
orthogonal neighbors have the same nonzero color. The authority is unchanged.

Ordinary inputs require at least one complete target; lawful distractors are
permitted. Identity-only grids remain valid rule inputs but are excluded from
this ordinary teaching domain. Explicit `no_pluses`, `plus_arms_mismatched`, and
`plus_already_filled` modes validate their actual narrow motif grammars. Metadata
no longer bypasses structural or semantic validation.

## Repair and audit disposition evidence

Previous source `e0ba1198c9dc3fee309404e08fbe36b31418e72b725d97ec30e0f8f3a4b22d15`
accepted a single arm (despite a docstring claiming two) and emitted only complete
positive targets. The source-bound horizontal-pair finding in
`evidence/review_index.json` is reproduced: the unchanged 5x5 pair is an identity
under Racket and fails the repaired ordinary validator. This is a teaching-domain
rejection, not an assertion that the input is unlawful for the reference rule.
The edited source requires four matching arms and teaches pair negatives beside
positive targets. Default layouts reserve two tiles and therefore refute both
horizontal-only and vertical-only pair rivals in each ordinary draw. Additional
space supplies a three-arm, mixed-color, or already-occupied-center distractor.
The 5x5 one-tile layout and explicit capacity-filling counts cannot also contain
separated distractors; these controls intentionally retain positive-only draws.

Audit evidence for the repair: `checks/68176b5eb124/axis-final/racket-labels.json`,
`axis-final/bounded-verification.json`, and task-local `tests/test_repair.py`. The evidence
index is retained unchanged for the owner's explicit resolution workflow.

## Controls and constraints

Dimensions are strict integers in 5..14; difficulty only selects default bounds.
`n_pluses` is exact, in 1..6 and subject to the number of separated 3x3 tiles.
Incompatible counts raise ValueError rather than silently clipping. The 5x5
layout has one slot; a 14x14 layout has sixteen. Default counts reserve two
negative slots when feasible. Sparse/dense density selects the minimum/maximum
default count; an explicit `n_pluses` wins.

`palette_size=8` fixes the available nonzero palette to colors 1..8, and
`position_bias=grid_aligned` fixes the motif lattice. `n_distinct_colors` counts
colors on complete target arms only and must be at most `n_pluses`; mismatch
and occupied-center distractors may add another color. Explicit distinct count
wins over style defaults. `single_plus` is the historical name for a single
**target color**, not a count override; `spread_pluses` and `rainbow` default to
one target color per plus, while rainbow orders the sampled palette. Helpful
`texture` names alias `palette_kind`; conflicting aliases raise ValueError.

Unknown controls and scalar coercions are rejected. Named identity modes honor
dimensions but reject inapplicable target count/color/density/style controls.
No reference change, new helper dependency, or training-admission claim is made.

## Focused verification

The pre-edit regression run produced 25 expected failures and 5 passes. The
repaired focused suite passes all 40 tests, including malformed-input rejection.
The bounded malformed-grid follow-up first reproduced two TypeErrors (37 other
cases passed), then added an early first-row type guard without changing generation. A bounded replay covers all sixteen
arm-presence masks, 212 exact-control cases over every dimension pair in 5..14
plus color counts, and twenty deterministic ordinary seeds. All twenty draws
refute both pair rivals. All 46 retained hand-made/generated inputs were executed
through the actual pinned Racket runtime and match the independent comparison.
The replay is `workspace/verify_repair.py`; compact receipts live under
`checks/68176b5eb124/`. Broad repository batteries and unrelated tests were not run.

## Override-gate compatibility

Numeric AXES valid domains remain machine-readable `1..6` and `1..8`; layout
capacity and target-color constraints live in separate descriptions. The narrow
`observe_overrides` derives dimensions, complete target count, and distinct
complete-target arm colors from the returned grid, excluding distractor colors.
A regression uses the actual shared `axis_domain_report`, required-observer
selection, and observation comparison to verify exact controls and detect an
incorrect count request. The pre-fix gate test failed (1 failed, 39 passed); the
final suite has 40 passes. No shared checker was edited.

`position_bias` is declared as the explicit singleton `["grid_aligned"]`, which
the shared checker classifies as `singleton`, retaining its expected warning
that a fixed policy cannot demonstrate variation. The inherited `never_probed`
classification is removed without inventing alternatives or marking an exact
control diagnostic. `palette_size=8` is also an intentional singleton. No full
override census or broad quality-gate pass is claimed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-bc14f34072838c20:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e0ba1198c9dc3fee309404e08fbe36b31418e72b725d97ec30e0f8f3a4b22d15`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted review-7c5cd8a4f0086a13 replaces degenerate plus patterns with four-arm positives/two-arm contrasts and structural validation. Reviewer reports40tests,46Racket cases,212controls and20seed rival checks. Finite one-tile/full-capacity limits remain; no owner rerun.

### Assessment or prior finding

## 68176b5eb124

**Status: Reproduced validator/teaching defect.** The authority fills a zero center only when all four orthogonal neighbors are equal and nonzero. The target `self_check` nevertheless accepts the 5×5 horizontal two-arm pattern below, and ordinary generation supplies complete positive pluses but no near-miss negatives:

```text
0 0 0 0 0
0 0 0 0 0
0 4 0 4 0
0 0 0 0 0
0 0 0 0 0
```

Authority rule hash `2dc205754ece` leaves the center zero; the plausible horizontal-pair rival fills it with 4. Evidence: `checks/audit/68176b5eb124/input.json`, `checks/audit/68176b5eb124/racket.json`, and `checks/audit/68176b5eb124/counterexample.json`. The retained counterexample records generator SHA-256 `e0ba1198c9dc3fee309404e08fbe36b31418e72b725d97ec30e0f8f3a4b22d15`, `self_check=[]`, exact outputs, and the supported apply command. This input is validator-admitted but not produced by the documented default generator, which is itself the teaching-coverage concern. Audit target left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-bc14f34072838c20-v0001/audit_assets.json), manifest SHA-256 `b15181d62a0626a11bf4c0b8787cf7f1acb7771446d8a0a506b87386c0b88849`.
<!-- arcpuzzles-current-audit-assessment:end -->
