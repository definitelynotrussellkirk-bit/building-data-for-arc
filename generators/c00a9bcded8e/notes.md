# Working notes: c00a9bcded8e

## Review scope

Assignment `review-eb0809aa18d40f47` reviewed the selected baseline generator
SHA-256 `26553b11387d21b5498e514ff1bb934aaa28db283c853d99e7b9987f6bd2bce6`.
The associated return `local-random-4c74c0d16e1f` was used only as a lead: it
explained the existing v2 noise, observable-axis, authority-sync, and rival
choices, but all claims were remeasured against the pinned source.

## Findings and repair

1. The v2.0.0 rectangle starts were fixed at three columns and one fixed row
   schedule for each row count. A solver that sampled those old anchors solved
   every generated three-example lesson without finding rectangles. Version
   2.1.0 allocates horizontal and vertical slack deterministically through the
   task RNG, preserving blank separation while varying every sampled layout.
2. Canonical targets include rectangle heights through 7 and widths through 8,
   while v2.0.0 generated at most height 6 and width 7. Version 2.1.0 expands
   widths to 3..8 and uses row-count-aware height ceilings of 7, 6, and 5 for
   2, 3, and 4 target rows so every layout still fits a 30x30 canvas.
3. The portable task test guessed a repository-relative canonical-data path and
   failed in the isolated runtime. It now uses the shipped
   `canonical_rule_source()` helper.
4. `CANONICAL_SHORTCUTS` previously named competitors that did not fit every
   canonical pair, and five presence-only semantic witnesses named no rival.
   The canonical-shortcut declaration is now empty; the five competitors remain
   lesson rivals, including the new `fixed_anchor` rival; every retained witness
   names and actually refutes a rival.

The selected Racket authority was not changed. `RULE_HASH` remains
`4732b1c1a64d`. Final generator SHA-256 is
`c84be892d0a5d8a723884382ee7ee43724840753860d38cd6a24a03afa37d1ff`.

## Retained probes and limits

`workspace/distribution_probe.py` independently extracts rectangles, checks
canonical dimension support and layout uniqueness, scores the declarations on
the actual generator, checks production three-demo windows, and rotates samples
through the query position in six-sample blocks. It is deliberately separate
from the Racket authority checks.

The generated curriculum intentionally teaches solid target rectangles and
exactly three columns per spatial row, although the selected oracle accepts
qualifying components at density >= 0.9 and can emit other row lengths. Finite
rival checks do not prove universal identifiability, and pooled layout signatures
can overlap across difficulty bands even though all 100 sampled layouts within
an individual band were distinct.
## Current reviewer considerations

Source SHA-256: `1b5e71b5ced5a6b441a44456d13ed93602561cb8017931f44ef0dcb0c7f9e097`.

# Decisions — c00a9bcded8e

Final generator: version `2.2.0`, SHA-256
`1b5e71b5ced5a6b441a44456d13ed93602561cb8017931f44ef0dcb0c7f9e097`.
The selected Racket authority is unchanged; `RULE_HASH` remains
`4732b1c1a64d`.

## D1 — Enforce exact request scalar types at the public boundary

**Observed defect.** The baseline accepted `True`, `False`, floats, strings, and
negative `sample_index` values. The values were coerced or reached modulo/RNG
logic, so calls outside the declared API silently produced lessons. The completed
baseline after run recorded 24 strict-scalar warnings in
`checks/after/checks/c00a9bcded8e_after_defect_lint.log`.

**Choice.** Validate before any scheduling, modulo, or `GenCtx` call. `seed` must
have exact type `int`; `sample_index` must have exact type `int` and be
nonnegative. `schedule_profile()` applies the same contract as `generate()` and
also validates difficulty.

**Original rationale.** Unknown. Python's `bool`-is-an-`int` behavior and helper
coercion likely made permissive behavior accidental rather than intentional.

**Alternatives rejected.** `int(value)` coercion was rejected because it makes
`1.75`, `"1"`, and booleans appear legitimate and collapses distinct caller
errors. Validating only inside `generate()` was rejected because callers can use
`schedule_profile()` independently.

**Failure modes and evidence.** The validator deliberately accepts arbitrarily
large and negative integer seeds because deterministic seed domains normally do;
only sample indices are nonnegative. Regression coverage is in
`tests/test_contract_repairs.py`; final defect lint and 70/70 portable tests are
green.

## D2 — Match canonical palette roles without erasing real canonical support

**Observed defect.** Baseline teaching templates used three colors for
`column_repeat`, up to six for `row_repeat`, and up to seven for `mixed`.
`defect_lint` reported a `palette_roles` structural mismatch because canonical
training examples use five target colors.

**Choice.** Use five shuffled target colors `a..e` in each 2–4-row template.
Each prefix uses all five and preserves a visible teaching distinction:

- `column_repeat`: first-column value repeats across the first two rows, while
  no row mirrors endpoints;
- `row_repeat`: at least one row mirrors its endpoints;
- `mixed`: neither condition holds.

The generator therefore produces exactly five target colors in ordinary
lessons. `_analyze()` accepts five **or six** because portable frozen fixtures
proved that the canonical held-out pair uses six.

**Original rationale.** The old templates optimized simple visual pattern
construction, but no retained note justified their palette cardinalities.

**Alternatives rejected.** Requiring exactly five everywhere was tried and
retained as a failed test run: two frozen canonical tests rejected the lawful
six-color held-out input (`checks/task-tests-final/result.json`). Returning to
3/6/7 colors was rejected because it restores the measured structural mismatch.
Sampling both five and six in production was deferred: the shared detector's
train/test support reporting is currently ambiguous, and a six-color branch
needs an explicit teaching/support decision rather than an unmeasured exception.

**Failure modes and evidence.** A solver can learn the five-color production
prior even though six-color inputs are lawful. This is reported as a limitation,
not hidden. The final profile floor is 60/60 exact, strict semantics 600/600,
and task tests 70/70.

## D3 — Preserve canonical Racket authority

No observed defect required a rule change. Rectangle selection, center
calculation, row grouping, and left-to-right row-major emission already match all
canonical labels. Editing the rule would have expanded risk and invalidated the
selected authority binding. The rule text and normalized `RULE_HASH
4732b1c1a64d` are unchanged; final rule smoke, Racket lint, and authority sync
are green.

## D4 — Keep the parametric extension isolated and episode-level

**Chosen parameter.** `horizontal_read_direction` with bounded values
`left_to_right` (canonical/default) and `right_to_left` (proposed). The value is
chosen once per episode. It changes only the executed within-row ordering, while
preserving target object roles, row grouping, noise, geometry, and output shape.

**Why this parameter.** It is a small semantic neighbor of the original task,
not a cosmetic palette reskin or unrelated composition. Demonstrations can
reliably distinguish it using asymmetric color rows.

**Alternatives considered.** Top-to-bottom versus bottom-to-top row order was
also plausible but would change the higher-level row ordering at the same time
as curriculum schedule assumptions. A target-color parameter was rejected as
mostly cosmetic. A rectangle-density threshold parameter was rejected because
current production draws solid rectangles and would not naturally identify the
threshold without changing the input grammar.

**Evidence and limits.** `checks/parametric/horizontal-read-direction-report.json`
executes both exact Racket programs and an independent Python mirror on two
complete 3-demo/1-query episodes: 8/8 pair agreement and six demonstrations that
all refute the rival setting. This remains a proposed prototype; it does not
modify production or approval.

## D5 — Retain ordered production; diagnose rather than claim rotations

Production assembly uses three demonstrations followed by one query. The final
small gate found 12/12 identifiable ordered lessons; the 300-lesson census found
300/300, with no declared-rival ambiguity. Query rotation was run because it is
cheap and informative, but its policy remains diagnostic: 0/1,200 ambiguous
rotations alongside 600 order-sensitive hook warnings. Therefore the return does
not claim arbitrary query-position support.

Requiring rotations immediately was rejected because the current hook expresses
features accumulated in an ordered three-example curriculum. A future schedule
change should either make those features position-invariant or explicitly
replace the hook, then rerun with required rotations.

## D6 — Preserve failures and use portable tests

The interrupted before battery, the completed 11/12 baseline after battery, and
the failed exactly-five canonical validator run are all retained. New tests use
`reviewer_support.find_root()` and `load_selected_generator()` so the same files
run in the repository and the isolated runtime. No frozen root fixture was
edited.

## Prior evidence used

The associated prior return `local-random-4c74c0d16e1f` and existing
`notes.md` were used only to understand earlier placement, dimension, and rival
decisions. The selected packet source and all final claims were independently
measured in this assignment.

## D7 — Replace the non-causal prototype with a native sequential family

Assignment `review-0b61f0cebf027e32` promotes a different parameter than the
historical horizontal-read-direction prototype. The native contract now uses
`finish = colors_only | highlight_largest_rectangle`. `colors_only` is bound to
the byte-exact selected canonical source. The alternative first performs the
canonical rectangle detection, measurement, grouping, and row-major ordering;
then it marks the output position of the unique largest qualifying rectangle
with color 9.

The input-dependent intermediate is the row-major table of rectangle records,
including occupied-cell count and output position. The retained
`highlight_largest_perimeter.rkt` program is a wrong-intermediate
counterfactual: it substitutes bounding-box perimeter for occupied area.
Constructed scenes force the two unique winners to differ, and the bounded
protected-Racket audit changes two final output cells in its retained witness.
This is materially stronger than merely reversing output order because the
second stage cannot choose its target before the first stage finds, measures,
and orders the rectangles.

The adapter independently supports 2–6 demonstrations and 1–4 queries, shares
identical inputs across settings, includes four retained queries, and places a
substantive 30×30 case at the end of the private source bank. The audit exercised
12 setting/count jobs, 92 generated pairs, 93 protected-Racket labels, 20
matched-input comparisons, 24 prefix checks, and 12 large-canvas jobs across
seeds 0 and 17. Among the finite declared hypotheses, only the intended setting
survived each demonstration set. This remains bounded evidence, not a universal
uniqueness or training-gain claim.

A first broad local pytest command could not collect the original generator test
because the lightweight packet runtime intentionally omits its full selected
source package. The correct copied, source-bound `task-tests` path passed 53
tests and 48 subtests; direct parametric tests passed 31 tests. The portability
warning in the new test was repaired by using `reviewer_support.find_root()` and
`canonical_path()`.
