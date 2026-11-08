# Review notes — review-e1ce8da604f6d683

## R1: semantic domain repair

Baseline v2.0.0 SHA-256:
`ec1df71e2e7418eb164dd3b10b9043b56a8558d5a3e8ad62e2eb7a818d2815aa`.
At seed 20261005, sample indices 0–99 in each of easy/medium/hard, 45 of 300
unique inputs had two or more seeds in one actual 4-connected non-wall region.
All 300 passed the old validator. The L-shaped presumed-room split does not
necessarily disconnect its regions; gray speckles can also change connectivity.
These are not proven wrong Racket labels: the reference defines a sequential
flood even for competing seeds. They violate the advertised simpler teaching
domain and introduce an unintended seed-order-dependent behavior.

Version 3 computes true components of a randomized gray field, selects distinct
seedable components of size at least two, and leaves a component unseeded.
There is no inference from geometric room lists. A 2,048-candidate rejection
budget fails loudly, never substitutes a fixed fallback or truncates seeds.

## R2: exact interface and canonical support

The only exact axes are height 7–20, width 7–20 and seed-color count 2–5.
All 2,352 band/height/width/count combinations passed independent observations
and domain/rival checks (14×14×4×3). Twenty additional seeds test 7×7 with five
colors. `None` means no override; booleans, floats, strings, out-of-range values,
and unknown axes are rejected. Seven previous controls were intentionally
retired: `n_walls`, `wall_orientation`, `palette_kind`, `wall_position_bias`,
`anchor_corner`, `asymmetry_force`, and `texture`. Downstream callers that pass
these must migrate; accepting them silently would preserve the original defect.

Original rationale beyond the old comments is unknown; associated_notes.jsonl
was empty and no prior return was used as evidence. A narrow L-split-only patch
was rejected because it would retain fake axes, band-dependent bounds, and a
very small family of straight-wall layouts. The new full legal domain is shared
by all bands; difficulty changes sampling weights, not override validity.

## R3: authority alignment, not a new reference rule

Canonical RULE_HASH is `1c419bef489c`. The canonical ledger and its outputs are
unchanged. Two selected base solution files had equivalent but text-divergent
`racket_target.target_code` fields; those active fields were synchronized to the
exact canonical program. Archival `raw_code` and all other JSON fields are
unchanged. The independent oracle matches all eight canonical labeled pairs
(four unique inputs) and all 1,200 saved final census Racket outputs.

## R4: explicit teaching contract and limitations

Each generated input refutes eight-connected filling, first-seed-only filling,
straight rays, bounding-rectangle filling, and Manhattan-nearest-seed coloring.
None fits every canonical pair, so `CANONICAL_SHORTCUTS` is deliberately empty.
Declarations are executed, not merely named. Three demonstrations are retained;
the source does not rely on a residue-specific witness schedule.

The final source-bound census contains 300 lessons, 1,200 unique Racket-labeled
inputs, and 1,200 whole-pair holdouts. No declared-rival ambiguity was found in
production or rotations. This is finite evidence, not a guarantee against
unlisted rivals or all possible draws. Filtering each board to refute all five
rivals biases geometry toward nontrivial paths and excludes many trivial or
rectangular scenes. Restricting seeds to distinct growing components with an
unseeded region intentionally excludes the full reference's competing-seed,
repeated-color, and singleton-seed domain. No model-training gain was measured.

Independent inspection of the final census found all eight permitted seed
colors, 940 inputs with a border seed and 260 with only interior seeds, so
neither a fixed seed palette nor an always-border seed is an invariant. Random
wall fields can still be visually denser than some canonical examples; canonical
shape/palette support and the explicit restrictions are not a similarity proof.

## Evidence and commands

The return's `checks/` retains before/intermediate/final failures and reports.
`workspace/review_probe.py` reproduces the 300-draw comparison;
`workspace/validate_census.py` independently reconciles all saved labels.
The generic opt-in `workspace/component_contract.py` does not import this
generator or Racket and detects the baseline collision. It is a prototype,
not an activated shared gate or training-approval change.

Run portable tests from packet root:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 6c8eefa043e1 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

Run a new final-source lesson census:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 6c8eefa043e1 --per-band 100 --rotate-query --timeout 1800 --out ../checks/new-census.json
```
## Current reviewer considerations

Source SHA-256: `9dbef586a5b24bfa7d3338f6d03c56419e34bb3d0e0767e8c716cc118cc3542e`.

# Decisions — review-1d4b54e76b4cb6aa

## R1-CALL-SCALARS: validate at the generator boundary

**Observed.** The immutable baseline battery was 11/12 green. Defect lint alone
failed because malformed `seed`, `sample_index`, and `difficulty` values reached
the shared context and were accepted. The failure was reproducible across 16
focused cases.

**Decision.** Add one narrow `_validate_call` function before `gen_ctx`:
`seed` and `sample_index` must have exact type `int`, sample index must be
nonnegative, and difficulty must be `None/easy/medium/hard`. Keep the task's
existing override validation and sampling logic intact.

**Why here.** The selected generator owns its public contract, while changing the
shared runtime would alter unrelated generators outside the assignment. The
boundary check fixes the source of this task's warnings without pretending that a
shared-policy change was approved.

**Rejected alternatives.** Coercion was rejected because `True`, `1.0`, and
numeric strings would remain ambiguous. A shared runtime edit was rejected as
out of scope. Ignoring the warning was rejected because malformed calls were
observable public behavior.

## R1-VERSION: retain `3.0.0`

The repair changes only rejection behavior for invalid calls. Twelve lawful calls
covering all bands and representative overrides are byte-for-byte identical before
and after. The valid sampling stream, canonical rule hash `1c419bef489c`, and
Racket authority are unchanged, so a generator semantic/version bump would be
misleading. The final source hash is
`9dbef586a5b24bfa7d3338f6d03c56419e34bb3d0e0767e8c716cc118cc3542e`.

## R2-PARAMETRIC-CONNECTIVITY: keep the extension separate

`connectivity` is a meaningful small rule parameter because four- versus
eight-neighbor propagation changes the inferred adjacency law while preserving
all object roles. It is chosen once per episode, defaults to canonical `four`, and
is tested on complete three-demo/one-query episodes. The bounded constructor
forces a diagonal-only satellite so the settings cannot collapse to the same
lesson.

The extension remains under `workspace/parametric/` rather than becoming a
production axis. The alternate program has only finite evidence and explicit
unique-seed/component constraints. Promoting it would require a separate rule,
validation, curriculum, and approval decision.

Rejected alternatives included changing wall color, seed palette, or grid size:
those vary presentation rather than the rule. A per-pair connectivity choice was
rejected because it would make one episode internally inconsistent.

## R3-COMPETING-SEED-LIMIT: report rather than silently broaden

The strongest canonical-compatible rival found is nearest-seed ownership within a
cardinal component. Canonical demonstrations do not separate it from sequential
capture, and the current production domain intentionally places at most one seed
in each true component. A custom 300-lesson census confirms 1,200/1,200 sampled
pairs remain indistinguishable.

The exact input `[[1,0,0,2]]` does separate the rules. The Racket authority gives
`[[1,1,1,2]]`; the rival gives `[[1,1,2,2]]`. Adding competing seeds to production
would reverse an explicit v3 teaching-domain decision and could introduce order-
dependent lessons. Therefore this return documents the gap and supplies a reusable
rival, but does not widen the approved domain.

## Lesson policy

Production lessons are ordered as three demonstrations followed by one query.
The final semantic gate checks 12 such lessons and runs all four diagnostic query
positions. A separate 300-lesson census uses required rotations and checks 1,200
query positions. Both report no ambiguity for declared/measured rivals. These
counts do not cover the undeclared nearest-seed rival described above.

## A1/A2: preserve adversarial audit boundaries

`8a67cd7d5f1e` and `195dfcc5b541` were inspected against their assigned current
hashes and left unchanged. A1 is a reproduced distribution/interface defect; A2
is a validator-clean but out-of-ordinary-sampler teaching counterexample. Passing
A2's 39 task tests does not close that gap, and A1's correct canonical histogram
labels do not excuse its contract failures.

## Stopping criterion

Stop after the selected source is all-green in the authoritative battery, focused
and portable tests pass, the final solve is source-bound, the proposed parameter
has executable evidence, both assigned audits have current-source receipts, and
the exact delta replays in a fresh extraction. No model-training improvement or
new rule approval is claimed.
