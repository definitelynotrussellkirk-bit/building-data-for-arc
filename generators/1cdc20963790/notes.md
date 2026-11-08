# Current notes: 1cdc20963790

## Intended rule and authority

The top row and left column are color headers.  For each interior cell, `1`
selects the header at the left of its row, `2` selects the header at the top of
its column, and `0` remains background.  The selected Racket authority was not
changed.  The generator pins canonical `RULE_HASH = "2d0911ecb918"`; the final
selected generator SHA-256 is
`b44a57e84c4b52d9436181af064675aeb0b0a4f309959b13f41b2c35031ea649`.

## Current sampling contract

Every ordinary draw is on the public canonical profile manifold:

- shape is `6x6`, `7x7`, or `7x8`;
- top-left is `0`;
- each header contains unique keys from `2..8`, both contain key `2`, and their
  union is exactly `2..8`;
- the interior contains only `0`, `1`, and `2`;
- there are exactly `2..6` row markers and `2..6` column markers;
- each branch includes key-mismatch evidence, key-2 identity evidence, and at
  least two distinct selected keys.

The only public exact axes are `shape_profile`, `row_markers`, and
`column_markers`.  Every Cartesian combination is legal in every difficulty
band, is drawn through `GenCtx`, and is recoverable with `observe_overrides`.
Unknown axes and invalid values fail loudly.  Four deterministic schedule
profiles (`balanced`, `row_heavy`, `column_heavy`, `edge_mix`) cycle with period
4; a lesson requests four demonstrations.

## Reversed decisions

The previous version advertised arbitrary `5..14` dimensions, density and
several descriptive singleton axes, plus three “degenerate texture” modes.  It
also allowed zero/duplicate/arbitrary `1..9` header keys.  Those choices were
reversed because they were not exact, often ignored, produced almost no
canonical-size/palette support, and admitted examples that weakened or removed
the two dispatch branches.  The replacement deliberately uses a narrower,
fully observable canonical-shaped manifold rather than preserving unsupported
breadth.

The old `self_check` only asked for some nonzero headers and one marker; it even
accepted the solid 2x2 grid retained in
`counterexamples/baseline-impostors.json`.  The current validator owns the full
input grammar and is also the strict-profile hook.

## Semantic teaching contract

`rule_mirror` is checked against the selected Racket rule.  Named rivals cover
swapped dispatch, all-row dispatch, all-column dispatch, preserving marker
colors, and fixed first-header shortcuts.  Named witnesses and
`lesson_identifiable` enforce their refutation, including query rotations.

Final evidence:

- all 12 after-repair battery stages green: `checks/after/`;
- 45 task-local tests green: `checks/task-tests/`;
- profile floor: 60/60 exact canonical profiles, 20/20 per band;
- semantic census: 600/600 strict inputs and all named witnesses fired in all
  bands;
- Racket smoke: 120 applications, 120/120 Python-mirror parity, 88 distinct
  outputs, no input mutation;
- lesson census: 300 lessons (100 per band), 1,500 unique labeled pairs/query
  rotations, zero declared-rival ambiguities or hook/scoring errors.

## Known limits and open findings

The finite rival set is not a proof that no other hypothesis can fit a lesson.
The generator intentionally excludes larger canvases, color 9, missing keys and
single-branch examples; those may be useful for a separate extrapolation split,
but they are not represented as ordinary training draws here.  Authority sync
still reports a divergent archival raw source; the canonical and selected task
rules are exact matches and execution parity passes.  Passing review checks does
not itself grant training approval.
## Current reviewer considerations

Source SHA-256: `b44a57e84c4b52d9436181af064675aeb0b0a4f309959b13f41b2c35031ea649`.

# Decisions for 1cdc20963790

## D1 — Preserve the selected Racket rule and pin its identity

**Original state.** The Python description matched the canonical task, but the
module had no `RULE_HASH`.  Authority sync also records an archival raw source
that differs textually from the selected task rule.

**Decision.** Keep the selected Racket rule unchanged and pin
`RULE_HASH = "2d0911ecb918"`.  Add a Python `rule_mirror` solely for executable
review contracts.

**Evidence.** The final authority-sync stage passes, canonical and selected
sources have the same rule hash, and 120 rule-smoke applications have 120/120
mirror parity (`checks/after/checks/1cdc20963790_after_rule_smoke.json`).

**Alternative rejected.** Rewriting the Racket rule was unnecessary and would
expand the assignment beyond an input-distribution repair.

## D2 — Replace the broad pseudo-controls with three exact controls

**Original state.** Eight axes were declared.  Difficulty-specific dimension
ranges rejected values that the public metadata called valid; density was
hard-coded by band; several enum-like axes had one token and were never probed;
degenerate texture paths ignored dimensions; unknown keys were swallowed.  The
baseline override checker reported 5,953 findings.

**Decision.** Expose only `shape_profile`, `row_markers`, and
`column_markers`.  Draw each through `GenCtx`, validate types/ranges before
generation, make all combinations legal in all bands, and recover every value
from pixels with `observe_overrides`.

**Alternatives considered.** Keeping `grid_h/grid_w` over 5..14 would preserve
breadth but continue generating profiles unlike every canonical example.  A
`marker_density` control is statistical rather than exact and was unnecessary
once exact branch counts were exposed.  Descriptive singleton axes were removed
rather than mislabeled as controls.

**Failure mode guarded.** A typo or ignored control can no longer silently
produce a valid-looking draw.  Boundary and Cartesian probes are covered by the
45 task tests and the green override stage.

## D3 — Sample the canonical size/palette manifold deliberately

**Original state.** Only 2 of 60 profile-floor draws matched a canonical
shape/palette profile; the hard band had 0 of 20 support.  Header keys could be
zero, repeated, or use colors 1 and 9, unlike the public examples.

**Decision.** Use only `6x6`, `7x7`, and `7x8`.  Make header keys unique within
each axis, require key 2 in both axes, and make the header union exactly colors
2..8.  With background 0 and marker colors 1/2, every draw has the canonical
nine-color palette.

**Alternatives rejected.** A mixed “canonical anchor plus arbitrary large
scenes” schedule was considered, but it would make strict membership and lesson
semantics needlessly bimodal.  Larger/extrapolative scenes should be a separately
named split rather than ordinary draws that obscure the training distribution.

**Measured result.** Final profile-floor support is 60/60 exact, including 20/20
in each difficulty band.

## D4 — Remove degenerate textures from ordinary generation

**Original state.** `no_keys`, `no_markers`, and `only_ones` were advertised as
valid textures.  The defect linter found domain overlap, and `only_ones` bypassed
normal validation.

**Decision.** Remove those modes and make every returned draw exercise both
semantic branches.  Do not treat intentionally malformed grids as valid
training examples.

**Alternative rejected.** Retaining them behind `meta` would still contaminate
the same generator contract and complicate all exact-axis guarantees.  Negative
examples belong in tests/counterexamples, not the production sampler.

## D5 — Own the full input grammar in `self_check`

**Original state.** The validator accepted a solid 2x2 all-2 grid and other
minimal impostors because it checked only for nonzero headers and any marker.

**Decision.** Validate dimensions, ARC cell types, top-left background, header
ranges/uniqueness/union, interior alphabet, branch counts, distinct selected
keys, mismatch witnesses, and key-2 identity witnesses.  Reuse it as
`strict_canonical_like` with `MIN_STRICT_FRAC = 1.0`.

**Counterexample.** `repo/generators/1cdc20963790/counterexamples/baseline-impostors.json`
is loaded by the focused test suite.

**Limitation.** This strict validator intentionally rejects lawful-looking
extrapolations outside the reviewed canonical-shaped training domain; that is a
distribution choice, not a statement that the Racket rule could not execute on
them.

## D6 — Make semantic distinctions explicit

**Decision.** Declare five plausible rivals: swapped branches, all-row, all-column,
preserve-marker, and fixed-first-header.  Construct every grid with witnesses
that refute them.  Cycle four schedule profiles and require four demonstrations;
`lesson_identifiable` checks labels, strict membership and rival survival.

**Why four demonstrations.** One strong grid often refutes all declared rivals,
but four examples make the intended curriculum stable across profile/count/shape
variation and match the four-state schedule.  Every cyclic start and every
held-out query position is covered in task tests.

**Measured result.** The semantic battery sampled 600 inputs with 100% strict
support and all witnesses firing.  A source-bound census materialized 300
lessons, 1,500 unique pairs and all 1,500 query rotations with zero ambiguity for
the declared rivals.

**Limitation.** Passing a finite rival library does not establish universal
induction.  Undeclared hypotheses remain possible.

## D7 — Test before implementation and retain failures

The new task suite was first run against the selected baseline and failed 44 of
45 tests for the intended missing contracts (`checks/task-tests-red/`).  After
the rewrite, all 45 pass.  The baseline battery and interrupted/resumed receipts
remain under `checks/before/`; the final battery is under `checks/after/`.

## D8 — Do not infer approval from green checks

All checks are reviewer evidence.  The generator remains subject to maintainer
intake and downstream training-admission policy.  No catalog approval or model
quality claim is made here.
