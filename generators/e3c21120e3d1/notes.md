# Working notes: e3c21120e3d1

Review `review-38a3c9f6f591dcde` replaced the imported 1.3.0 curriculum with
version 2.0.0.  The canonical Racket rule was not changed.

Key retained artifacts:

- `tests/test_generator_e3c21120e3d1.py` — source-bound regression contract;
- `workspace/review_probe.py` — exact-axis and complete-lesson replay tool;
- packet-root `REVIEW.md` and `DECISIONS.md` — findings and rationale;
- packet-root `checks/after/`, `checks/lesson-census.json`, and
  `checks/review-probe.json` — final evidence.

Do not broaden axes or admit symmetric inputs without rerunning Racket-backed
semantic checks, every cyclic lesson start, and all query rotations.  Python's
`rule_mirror` is diagnostic only; the pinned Racket rule remains authority.
## Current reviewer considerations

Source SHA-256: `a37cbf390342860185d47fd705191059fe6a527d2e5323b4127ed94efd1ce528`.

# Decisions — e3c21120e3d1

## D1 — Treat the executable rule as exact whole-grid transpose

The canonical examples and Racket authority agree on `output[c][r] = input[r][c]`.
The original generator's broader texture narrative was not needed to express
that rule and created invalid or uninformative cases.  The repair pins
`RULE_HASH = "f5d00e3992ee"` and leaves authority bytes unchanged.

Rejected alternative: change the Racket source or canonical ledger to match the
old validator.  The defect was in the curriculum, not the authority.

## D2 — Replace eight misleading controls with three exact semantic axes

Only input height, input width, and distinct nonzero color count are exposed.
Their full domains are `3..8`, `3..8`, and `1..2`; every Cartesian combination
is constructible.  Unknown controls and bad types raise rather than silently
falling back.

The original rationale for dead textures and contradictory difficulty ranges is
not recorded.  Preserving them for compatibility was rejected because callers
could not infer whether a requested intervention was honored.

## D3 — Anchor defaults to all canonical input profiles

The schedule uses the four labeled canonical input scales and their observed
component morphologies without copying canonical pixels: two blobs on `4×7`, a
four-cell blob plus two same-color points on `5×6` and `6×4`, and four one-color
points on `3×8`.  This keeps scale and sparsity evidence while randomizing
colors, positions, and polyomino orientation.

Rejected alternative: a generic random sparse sampler only.  It can be valid but
needlessly drift from the small canonical support and makes profile-floor
failures harder to interpret.

## D4 — Use constructive component placement

Connected polyomino variants are placed with same-color component separation.
A bounded internal search chooses among feasible placements; every returned grid
is checked against the full semantic validator before release.  Exact override
calls switch to a compact generic component contract feasible even on `3×3`.

Rejected alternative: rejection-sample arbitrary colored cells.  It produced
long tails, accidental component merging, symmetric grids, and poor causal
control over failures.

## D5 — Make semantic ambiguity an input validity condition

Every generated input must make transpose differ from identity, clockwise,
counterclockwise, and 180-degree rotations, left-right and up-down flips, and
anti-transpose.  These functions are executable and reused by witnesses and
lesson diagnostics rather than duplicated as names.

Tradeoff: an individually symmetric but otherwise legal transpose example is
excluded, even though a larger lesson might disambiguate it.  For this compact
training curriculum, stronger per-example evidence is preferable and matches
the user's goal of high-value data.

## D6 — Use a four-slot schedule and phase difficulty

`EXAMPLES_NEEDED = 3`; a lesson with three demos plus one query spans four
consecutive profiles.  Each four-example window therefore contains the observed
branches.  Difficulty changes the phase offset, making the control live without
claiming a new mathematical difficulty model.

Rejected alternative: random profile selection.  It would require a much larger
census and could produce local windows missing a branch.

## D7 — Separate Racket authority from Python diagnostics

`rule_mirror` provides fresh outputs for tests, rival scoring, and the portable
probe.  Racket-backed rule smoke, semantic checks, and `arcpuzzles apply` remain
the label authority.  Reports state this limitation explicitly so Python is not
mistaken for an independent oracle.

## D8 — Repair test-first and preserve the red evidence

The new task-local contract tests were written before the source replacement.
They failed on the missing rule pin, rejected one-color canonical case,
difficulty-dependent override mismatch, unknown-key acceptance, ignored axes,
and absent observability.  The retained red log is
`checks/task_tests_red.log`; the final suite has 63 passing tests.

## D9 — Add a reusable full-contract probe

`workspace/review_probe.py` imports the selected module dynamically and uses
`reviewer_support` for canonical discovery.  It enumerates all integer-axis
values, all four bands, actual `LESSON_COMPETITORS`, cyclic starts, and query
positions.  It emits source hash, counts, exact failures, and limitations as
JSON, and exits nonzero on a finding.

Rejected alternative: a one-off notebook or copied rival list.  Both become
stale when the generator changes and are harder for the next agent to replay.

## D10 — Preserve solve integrity

The post-repair solve was prepared only after the final generator hash was
frozen.  During the solve, only visible challenge files were used; prior rule
exposure was recorded as `yes`.  One transpose implementation matched all three
visible demonstrations, so no artificial negative attempt was added.

## D11 — Keep audits read-only and authority-backed

The two drawn targets were not patched.  Each finding has exact generator/rule
hashes, validator status, supported Racket output, and a reproducible shortcut or
rival in `checks/audit/`.  Their failures do not alter the selected task's
acceptance result.

## D12 — Limits and stopping rule

Finite seed and rival coverage cannot prove universal teachability.  The repair
stopped after the final source passed all twelve battery stages, 63 task tests,
required query rotations, the 300-lesson census, and the stronger portable
probe; the exposed solve remained bound to the same hash.  No model training was
run, and private solve labels were not revealed.
