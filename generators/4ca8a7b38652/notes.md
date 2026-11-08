# Current notes: `4ca8a7b38652`

## Intended rule

Count the distinct **nonzero** input colors. If that count is `n`, replace every
input cell with an `n × n` block of the same value. Zero is copied into the
output like any other value but is excluded from the scale count. The selected
canonical rule is pinned by `RULE_HASH = "2e2cb8677499"`.

## Review change

Version 2.0.1 sampled fully colored 2–5 grids, rejected every canonical input
because canonical grids contain zero, advertised controls it did not reliably
honor, lacked a rule hash, and supplied no lesson-level shortcut contract.
Version 3.0.0 instead emits 3×3 canonical-profile grids with exactly 2–4
nonzero colors. A five-position schedule mixes zero-present and zero-free
examples and redundantly supplies scale-2 and scale-4 cases so that any single
query holdout still refutes the declared rivals.

The selected base `target_code` was synchronized byte-for-byte to the canonical
`program_solution`; the earlier executable `raw_code` remains archival evidence.
The canonical Racket authority and its behavior were not changed. No prior
return ZIP was used as a semantic lead. The in-packet accepted generator
`7a37505e7bd0` was consulted only for the selected/archival authority metadata
convention.

## Decisions and assumptions

- Exact public axes are only `color_count` (2–4) and `zero_present` (boolean).
  Unknown axes, invalid types/ranges, and unknown difficulty names fail closed.
- Zero-present templates cover every sorted canonical frequency profile.
  Zero-free templates are deliberate counterexamples to the strongest
  canonical-fitting shortcut, “count all colors then subtract one.”
- `self_check` enforces the stated 3×3 teaching manifold, including row/column
  variation and rejection of the degenerate two-color solid-2×2 partition.
- The declared Python mirror is test support only; Racket remains label authority.
- `lesson_identifiable` checks labels, the zero-present/zero-free contrast,
  scale-2/scale-4 coverage, and every declared executable rival.

## Evidence and limits

Final generator SHA-256:
`8f0857a63cbe9f72594705d5544232152b6b91c46a1c06fb97ff4427397efb85`.
Focused tests, the full battery, the 300-lesson rotation census, and exhaustive
five-residue fixed-seed schedule census are retained under `checks/` in the
review return. The exact strongest-shortcut witness is
`counterexamples/always_subtract_one.json`.

The teaching distribution intentionally remains 3×3 because every canonical
input is 3×3; it does not establish shape generalization for the more general
Racket program. Rival checks are finite and do not prove unique induction over
all possible programs. No repair blocker remains.
## Current reviewer considerations

Source SHA-256: `9e39ddd0012e5dba7be9e7ae10f3ac8de0ca736e8c7bfad79a3535b4ae352ac5`.

# Decisions: 4ca8a7b38652

## D1 — Reject non-exact seed and index scalars at the task boundary

**Prior choice:** `generate` passed `seed` and `sample_index` directly into
`gen_ctx`. The original rationale is not recorded; Python consequently treated
booleans as integers, and negative sample indices were accepted.

**New choice:** require exact `int` values (not `bool`, float, or string) and a
nonnegative `sample_index` before any random draw.

**Evidence:** the before battery's `strict-scalar` findings and the test-first
regression in `tests/test_generator_4ca8a7b38652.py`. The final defect lint is
green.

**Rejected alternative:** change shared `gen_ctx` in this task return. That would
alter every generator and exceed the selected-task edit boundary. Shared
validation is nevertheless recommended as feedback F2.

**Limitation:** the repair intentionally does not impose a maximum seed/index;
large nonnegative integers remain deterministic and are supported by the current
context implementation.

## D2 — Preserve all production distribution choices

**Choice:** retain the existing 3×3 inputs, `color_count` axis, `zero_present`
axis, five-example schedule, palette selection, canonical-profile prior, and
semantic rivals unchanged.

**Reason:** the final distribution, profile floor, grammar, diversity, overrides,
Racket smoke, and source-bound semantic contract already pass. The reproduced
bug is call validation, not data semantics. Changing input geometry or schedule
would add risk without addressing it.

**Failure mode considered:** the canonical shortcut `distinct(all)-1`. The
current schedule already emits zero-free examples at offsets 1 and 3, so a full
lesson teaches why zero must be excluded.

## D3 — Keep the canonical Racket authority unchanged

**Choice:** no Racket edit. `RULE_HASH=2e2cb8677499`; canonical source SHA-256 is
`d91346f9bf6dbc10251783f3ea5e16533a63631db37bec02b3f21d3735d214c6`.

**Reason:** Python mirror, canonical labels, rule smoke, Racket lint, and
authority-sync all agree. The production defect occurs before generation and is
independent of the transformation.

**Rejected alternative:** encode seed/index validation in the Racket rule. The
rule receives only a grid and cannot enforce generator-call types.

## D4 — Parameterize color-count scope, not geometry

**Proposed parameter:** `count_scope ∈ {nonzero, all}` selected once per episode.
The canonical default counts distinct nonzero colors; the variant counts all
distinct colors. Both then apply the same cell-wise square upscale.

**Reason:** this is a small, meaningful variation of the rule's decision point
while preserving object roles and output mechanism. It avoids unrelated changes
to input size, interpolation, or output packing.

**Rejected alternatives:**

- `scale_offset`: an arbitrary arithmetic change that weakens the original
  “count visible categories” reasoning.
- non-square or anisotropic expansion: changes the output operation rather than
  parameterizing the original rule.
- a production `count_scope` override: would mix incompatible labels under one
  selected canonical authority and is therefore kept out of production.

**Evidence:** `workspace/parametric/prototype.py`, its focused tests, and
`checks/parametric-count-scope/evidence.json`.

## D5 — Use mixed zero-present/zero-free demonstrations

**Choice:** four demonstrations include both regimes; one query is held out.
Inputs do not depend on the hidden setting.

**Reason:** zero-present pairs distinguish the two count scopes, while zero-free
pairs show that the rules coincide on part of the domain. Choosing inputs first
prevents label-setting leakage.

**Failure mode:** an episode containing only zero-free examples cannot identify
`count_scope`; the prototype asserts that the four demonstrations refute the
other setting and documents this limit.

## D6 — Treat schedule enumeration as final semantic evidence

**Choice:** retain the first after battery failure, then rerun the complete
battery with `--enumerate-schedule-period --schedule-seed 0`.

**Reason:** the first run showed one policy warning because a declared finite
schedule was sampled rather than enumerated. Reclassifying the warning or hiding
it would be weaker than checking every start and query rotation.

**Additional evidence:** the independent 100-lessons-per-band rotated-query
census found no ambiguity in 1,800 query rotations.

## D7 — Audit targets remain findings-only

No source under `generators/67702540cb95/` or
`generators/4f09f8bfa35a/` was changed. Their deterministic reproducers live only
under `checks/audit/`, and the findings are separated in `AUDIT.md`.

## Current alternate scale-offset proposal

Unselected stale-baseline proposal. Issued generator8f0857a6 differs from current approved9e39ddd0. Current source already has exactly the requested literal-integer/nonnegative-index checks; returned generator differs only in comments/error messages and does not add behavior. Applying whole delta would collide with the retained count_scope prototype and its owner public-name correction. Preserve distinct scale offset-1/0/+1 proposal without replacing current source/tests/prototype. Reviewer61 portable/fresh tests,12/12 strict battery,64 valid baseline fingerprints unchanged,300 lessons/1800 rotations clean,all five starts/90 rotations at one seed. Offset prototype12 ordered episodes/72 primary Racket labels,297 total calls,108 wrong rival combinations refuted;arbitrary prototype rotations unknown. Optional root suite1002 pass/17 fail/3 skip remains failed,baseline not rerun. Source and evidence retention is not a rebase,variant approval,training admission or current-prototype increment. Retained at `workspace/proposals/review-ad71de162668ae32/manifest.json`.


## Current review — 2026-10-23 — `review-739adb393a726593`

This section records the current source and evidence; preceding decisions,
source hashes, audit IDs, and proposal receipts retain their historical scope.
The selected production generator is **unchanged** at SHA-256
`9e39ddd0012e5dba7be9e7ae10f3ac8de0ca736e8c7bfad79a3535b4ae352ac5`.
The canonical `RULE_HASH` is still `2e2cb8677499`, and the exact canonical
Racket program SHA-256 is
`d91346f9bf6dbc10251783f3ea5e16533a63631db37bec02b3f21d3735d214c6`.
No older historical hash above is being asserted as the current source.

### Current prototype choice and superseded one-query note

The earlier **D5 one-query choice is superseded for the current count-scope
prototype**. `workspace/parametric/prototype.py` now exposes independent
`--train`/`--test` counts, both defaulting to **4**, and retains one hidden
`count_scope ∈ {nonzero, all}` throughout every episode. The canonical default
still uses the exact registered Racket text. Input draws are independent of the
setting; a zero-present first demonstration distinguishes the two settings and
zero-free examples show their invariant region. Positive counts are bounded to
64 total pairs, with at most 64 candidate attempts per unique input. Exhaustion
raises instead of cloning queries or returning a short episode.

Current prototype SHA-256:
`d5fe57a4181bf4b3ce9fb4b65455aa76437a287d56987dc6de9c84eecc1d861c`.
Its six retained episodes cover seed pairs 0/1, 16/17, and 42/43 with 4/4, 4/4,
and 6/4 counts: **28 demonstrations, 24 queries, 52 distinct inputs overall,
and 104 protected Racket evaluations**. Every primary label and rival
prediction was executed; all queries passed checks using demonstrations alone.
The independent inspector verifies source/program/file hashes, lawful inputs,
counts, uniqueness, and the public/private boundary. Exact commands and evidence
are in `checks/parametric-v2/implementation-receipt.json` and
`checks/parametric-v2/evidence-audit.json` in this review return.

The export constructor explicitly projects visible pair fields under a generic
schema; public names depend only on visible demonstration inputs/outputs and
query inputs. Hidden parameters, seeds, references, query answers, and private
pair fields cannot enter that public projection or influence names. The review
also fixes the exact-file hash mismatch caused by appending an un-hashed newline
to `.rkt` exports, and adds bounded duplicate admission checks. Failing receipts
precede the fixes. The separate stale-baseline scale-offset proposal above is
preserved; it neither replaces this prototype nor inherits its current evidence.

### Current canonical checks and retained runtime failures

The official final after battery is **12/12 green** and the separate official
task-test run is **37 passed in 18.37 seconds**. The production seed-17 four-query
probe has **5 demonstrations, 4 queries, 9 distinct inputs, and 9 Racket-verified
accepted labels**, with passing per-query demo-only hook/rival checks. Accepted
indices are 3–11 because the first three attempts reported `RacketBridgeError`
process deaths; their cause is unconfirmed under the observed resource pressure.
Those failures are retained in `checks/four-query.jsonl` and
`checks/four-query-summary.json` rather than being treated as semantic rejection.

The 300-lesson census passed production and required-rotation checks with
**1,800 labels, 1,800 rotations, 1,656 exact unique inputs**, and zero ambiguity,
warnings, or errors. The compressed source-bound report is retained as
`checks/lesson-census.json.gz`, with its compression manifest and compact summary.
The after battery's complete fixed-seed-0 five-residue census checks **15 lessons,
90 rotations, and 27 unique inputs**. The initial incomplete before battery
(exit 247) remains under `checks/before/`; OOM/resource pressure is an inference,
not a confirmed explanation of every failed process.

### Current scope and pending maintainer decisions

The input domain remains 3×3 with 2–4 nonzero colors. Canonical approval does not
approve the `all` variant, and bounded finite-rival checks establish neither
all-seed identifiability nor a measured model-learning benefit or training
admission. Fresh review reports no Critical or Important prototype issue.

The optional archive-backed return builder is a separate **proposed tooling
extension**, not stock sparse-workspace support. Its cache-symlink minor issue
was fixed and 28 synthetic tests pass. Full real-archive verification and fresh
replay are separate release gates whose actual outcomes are recorded in this
return's `RESULTS.json` and final `REVIEW.md`; these synthetic tests do not certify
them. Adoption of the optional shared interface remains a maintainer decision.
The current assigned audits are `ebd08d719ed6` and `05b5a82ace36`, findings-only;
Racket confirmation status must follow their final retained receipts. Allocation
feedback F3 covers three source-bound records and does not rank external sources
or change allocation/admission policy.
