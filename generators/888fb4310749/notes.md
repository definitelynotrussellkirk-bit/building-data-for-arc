# Current notes: 888fb4310749

## Intended rule and authority

The input contains one solid monochromatic nonzero rectangle on black. Let its
bounding-box height and width be `h` and `w`, with period `h + w`. Repeat the
source rectangle in its original orientation and color along both diagonals;
place the adjacent quarter-turned `w × h` rectangle in color
`9 - source_color`; clip stamps at the canvas; paint source-orientation stamps
last.

`RULE_HASH = 2e44fadee3f2` is unchanged. The canonical Racket behavior is
unchanged. The base solution's `racket_target.target_code` was synchronized to
the canonical pretty-printed text only; `raw_code`, normalized tokens, labels,
and behavior stayed fixed. See `checks/authority-sync-proposal.json` and
`checks/authority-sync-apply.log`.

## Repaired production generator

- `seed` must be a literal integer. `sample_index` must be a nonnegative literal
  integer. Booleans, floats, strings, and negative indices fail closed.
- Every fourth default sample is an exact canonical canvas-profile anchor.
  Easy/medium alternate the 16×16 public families; hard alternates 23×23 and
  26×26 families. Placement and orientation still vary. Explicit
  `scene_profile` requests preserve the exact public fixtures.
- The semantic contract declares three rivals: identity/no stamping,
  source-orientation blocks only, and canonical geometry with a hard-coded 3/6
  companion color. Corresponding witnesses are executable against the real
  rule mirror.
- `LESSON_SCHEDULE_PERIOD = 2`. Every odd default sample is drawn from the
  general-profile domain and recolored to a deterministic non-3/6 source color.
  Choosing the feasible profile domain before the draw preserves keyed-axis
  provenance. Thus every four consecutive production pairs contain at least two
  color-law witnesses, and any three demonstrations retained by a query rotation
  contain at least one. Explicit profile overrides are not recolored.
- `lesson_identifiable` checks all three declared rivals and rejects any custom
  lesson where a rival survives the demonstrations but differs on the query.

The canonical execution path (`rule_mirror`) was not changed. `VERSION` remains
`3.0.0` because the selected generator's explicit public-profile fixtures and
canonical behavior remain the same; the repair changes default sampling and
teaching guarantees rather than defining a new rule.

## Strongest canonical shortcut

All four labeled canonical inputs use source color 3 or 6. Therefore a rival can
copy the entire diagonal geometry while hard-coding the companion color to the
other member of `{3, 6}`. It fits every canonical pair but fails on generated
non-3/6 colors. The exact source-color-1 witness is retained at
`counterexamples/fixed_36_color_shortcut.json` and is covered by focused tests.
The pre-schedule 300-lesson census reproduced this defect in 36 ordered lessons
and 141/1,200 rotations; its source-bound companion and compressed full report
are under `checks/lesson-census-final*`. The final source-bound census is under
`checks/lesson-census-final-cf61*`; it requires all rotations and retains exact
materialized lessons.

## Distribution and teaching limits

- Exact-profile anchors are scheduled for support, not as a claim that the
  overall mixture matches ARC-wide size frequencies.
- The period-2 color guarantee applies to the default consecutive production
  sampler. Arbitrary hand-picked or nonconsecutive lessons must still call
  `lesson_identifiable`.
- Finite rivals and census runs do not prove unique induction against every
  possible program.
- The legacy frozen root test still uses a fixed `__file__.parents[...]`
  canonical-data path and fails portable task-test preflight before pytest. It
  was intentionally left unchanged for maintainer migration.

## Proposed parametric extension

`workspace/parametric/prototype.py` is an isolated **prototype**, not a
production or authority change. It selects one episode-level `diagonal_mode`:
`both` (canonical default), `falling`, or `rising`. The source extraction,
period, rotation, complement color, clipping, and paint precedence remain
fixed. Evidence under `checks/parametric/888fb4310749-diagonal-mode-v1/`
contains three complete Racket-labelled episodes, exact rule texts/hashes, a
cross-mode witness, and pairwise rival checks. All four canonical labels replay
under `both`.


## Completed prototype public export and four-query repair

The source-bound follow-up in
`evidence/parametric-public-identifiers-pending-0c40bbcc130315b0/manifest.json`
is now implemented in the isolated prototype. Public challenges are serialized
with `reviewer_support.public_challenge_bytes`; each public filename and ID is
the SHA-256 of those exact visible bytes. Batch export sorts by public ID and
rejects duplicate visible payloads instead of overwriting or silently
collapsing them. Hidden settings, seeds, programs, rival predictions, and query
answers remain private.

Episodes now expose independent bounded demonstration/query counts (1 through
8 each), defaulting to three demonstrations and four distinct queries. Every
retained input separates all three declared diagonal modes, every query is
checked against both rivals, and demonstrations refute each rival before any
query answer is used. Racket-backed evidence is retained under
`checks/parametric/888fb4310749-diagonal-mode-v2/`: three complete episodes,
4/4 canonical labels, exact instantiated programs, byte-addressed public files,
and a cross-mode witness. The selected production generator, canonical rule,
`RULE_HASH`, and approval state remain unchanged. This is still a finite-rival,
unapproved prototype rather than a production axis or training-admission claim.
## Current reviewer considerations

Source SHA-256: `cf61a8a04194e393fda55318233daed0af194c0c9ee7f47e9377885d19779b0d`.

# Decisions for 888fb4310749

## D1 — Preserve the canonical rule

**Decision.** Keep `RULE_HASH = 2e44fadee3f2` and leave `rule_mirror` semantics
unchanged.

**Why.** Canonical labels, the executable Racket rule, and the existing Python
mirror already agree. The observed defects were call validation, distribution,
authority text drift, and teaching support—not rule behavior.

**Rejected alternative.** Rewriting the Racket program or simplifying its stamp
loops would create unnecessary authority risk. The only base-solution edit is
exact-text synchronization of `target_code`; `raw_code` and behavior are fixed.

**Failure mode if wrong.** A semantic rule edit could silently invalidate all
canonical outputs and prior evidence.

## D2 — Add deterministic exact-profile anchors every fourth sample

**Decision.** Schedule a canonical canvas-profile nuisance when
`sample_index % 4 == 0`, with easy/medium using the 16×16 families and hard using
23×23/26×26 families.

**Why.** The initial after battery found zero guaranteed exact-profile support in
some bands. A sparse anchor schedule guarantees support while leaving 75% of the
default stream on the broad mixture. Placement/orientation nuisance prevents
literal replay.

**Rejected alternatives.** Literal canonical inputs would be memorization-prone;
forcing all samples to canonical dimensions would collapse diversity; widening
only random ranges would not guarantee the profile-floor gate.

**Measured result.** The completed pre-census battery measured 15/60 exact hits
and 33/60 canonical-envelope hits with every band represented. The final
source-bound rerun is recorded under the latest `checks/after-*` directory.

## D3 — Bind all three semantic rivals

**Decision.** Declare identity, source-blocks-only, and fixed-3/6-complement as
both semantic rivals and lesson competitors.

**Why.** The first two are refuted by every normal output. The third is the
strongest canonical-fitting shortcut and must be checked explicitly rather than
left as a global witness only.

**Rejected alternative.** Omitting fixed-3/6 from `LESSON_COMPETITORS` allowed
the hook to approve lessons that the source-bound census independently marked
ambiguous.

## D4 — Use a period-2 color curriculum

**Decision.** On default generation only, choose odd samples from the general
profile domain and force a non-3/6 source color from `{1,2,4,5,7,8}`; preserve
even samples and every explicit `scene_profile` override.

**Why.** In any four consecutive indices there are two odd indices. Removing any
one query leaves at least one non-3/6 demonstration, so the fixed-3/6 shortcut is
refuted for ordered production and every query rotation. This composes cleanly
with the period-4 exact-profile anchors, which remain on even residue 0.

**Rejected alternatives.** Forcing every sample non-3/6 would weaken canonical
color support. Randomly increasing non-3/6 probability would not eliminate
ambiguous windows. Recoloring an odd public-family draw after selection caused
keyed-axis provenance drift, so the sampler now selects a feasible general-only
domain before drawing. Resampling only after a hook failure would make accepted
sample-index provenance harder to reason about and would not provide an
exhaustible schedule contract.

**Limits.** The guarantee is for consecutive default production lessons.
Custom/nonconsecutive assembly must call `lesson_identifiable`.

## D5 — Fail closed on scalar call controls

**Decision.** Accept only literal integer seeds and nonnegative literal integer
sample indices.

**Why.** The initial defect-lint run showed that booleans/floats/strings could
enter a deterministic API that claims integer controls. Strict validation is
small, observable, and portable.

## D6 — Synchronize authority text, not behavior

**Decision.** Apply the authority-sync proposal only to
`racket_target.target_code` in
`shared/data/base/solutions/training/fd4b2b02__888fb4310749.json`.

**Why.** The authority gate found whitespace-only divergence from the canonical
pretty-printed program. The dry-run and apply receipt show unchanged normalized
code, `raw_code`, rule hash, and behavior.

## D7 — Keep the diagonal-mode work isolated

**Decision.** Return `diagonal_mode ∈ {both, falling, rising}` as a proposed
prototype under `workspace/parametric/`; do not add it to the selected generator
or canonical authority.

**Why.** It is a small episode-level rule parameter that preserves object roles
and all non-diagonal reasoning. Each setting has a materialized Racket program,
a complete episode, and demonstrations that distinguish both rivals.

**Limits.** Evidence covers one deterministic episode per setting and the four
canonical labels under `both`; undeclared modes/rivals are unproven.

## D8 — Do not edit the frozen portable fixture

**Decision.** Leave
`tests/test_generator_888fb4310749.py:16` unchanged even though its fixed parent
depth breaks in the portable task-test runtime.

**Why.** The assignment explicitly marks the root fixture frozen and assigns its
migration to the library maintainer. New tests use `reviewer_support.find_root`,
`canonical_pairs`, and `load_selected_generator` and pass independently.

**Consequence.** Overall completion is reported `blocked`; the portable aggregate
cannot be called a pass even though the new focused tests and full battery pass.

## D9 — No changes to adversarial audit targets

Both drawn audit targets passed their retained task suites and source-bound
300-input/75-window probes. No actionable defect was reproduced, so their
sources remain byte-identical to the assigned hashes. See `AUDIT.md`.

## D10 — Preserve keyed-axis provenance at the draw boundary

**Decision.** Odd default curriculum samples exclude `PUBLIC_PROFILES` before the
`scene_profile` draw; even samples, period-4 exact-profile anchors, and explicit
profile overrides keep their prior domains.

**Why.** Recoloring a drawn public family changes the observable family signature,
so the override gate reproduced three draw/return mismatches in 90 sampled calls.
Restricting the feasible domain before the keyed draw keeps the recorded and
observable axis equal without weakening the period-2 color witness guarantee.

**Evidence.** `checks/axis-provenance-tdd/red.log` reproduces the mismatch;
`green.log`, `focused-green.log` (32/32), and the final override/full-battery
receipts verify the repair.

## D11 — Complete the prototype writer without promoting the parameter

**Decision.** Finish the isolated diagonal-mode prototype with exact visible-byte
public IDs, duplicate rejection, sorted exports, and a default 3-demo/4-query
episode; do not modify `generator.py`, canonical Racket, `RULE_HASH`, or approval.

**Why.** The retained pending manifest and current return contract identify two
specific gaps: setting-associated ordinal public paths and a single hard-coded
query. Content addressing removes the hidden-setting path channel, while four
independently checked queries provide useful parameter support without changing
the canonical task.

**Evidence.** The focused test file passes 27/27. The retained Racket run under
`checks/parametric/888fb4310749-diagonal-mode-v2/` has three complete episodes,
4/4 canonical replays, all labels/rivals executed in Racket, unique sorted
public IDs, and filenames equal to SHA-256 of the exact public bytes.

**Limits.** Only the declared `both`, `falling`, and `rising` rivals are checked.
The prototype remains unapproved and isolated from production generation.

Current source-bound export inspection: `generators/888fb4310749/evidence/parametric-public-export-inspection-0a50a3d564bf35bf/manifest.json`. The earlier export/count finding is resolved only for these corrected prototype bytes; all other audits and approval boundaries remain unchanged.
