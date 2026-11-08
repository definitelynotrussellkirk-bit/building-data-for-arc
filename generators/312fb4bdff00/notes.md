# Review notes: 312fb4bdff00

Current assignment `review-c57ca56ab5863cee`; version `3.0.0` → `3.1.0`.
Current generator SHA-256: `e2d85dedd4b4a2fb2a5bacb6c24ea9c25113bd95ba52917e7410449e376c3c97`. Previous source SHA-256:
`ffbe31ada4158793dd6e1326c0066e599b9c7178bc9bec8e1b5637c878f02278`. Canonical Racket rule pin `cc8c5c7301a4` is unchanged.

## Current decision

Keep the rule and input domain unchanged, but make absence an explicit default
schedule phase. The default cycle is now `multiple`, `absence`,
`translated_single`; six consecutive pairs contain two of each. With five
examples and one query (`EXAMPLES_NEEDED = 5`), every cyclic query choice leaves
at least one no-match demonstration, one translated-single demonstration and one
multiple-match/precedence demonstration.

The new declared rival `copy_query_on_absence` performs the real matching rule
when a candidate matches but returns the recolored query instead of `[[0]]` on
absence. It fits all three canonical pairs. `absent_equal_count_match` now binds
both this rival and `count_only_copy`.

Explicit `match_count` overrides still describe one input rather than a complete
lesson. In particular, `match_count=1` remains able to request an aligned single
match; default teaching no longer spends a schedule slot on that case.

## Defect and root cause

The retained audit witness used seed `14`, difficulty `easy`, start `0`. Version
3.0 produced match counts `[1, 2, 1, 1, 2, 0]`. Holding out offset 5 left five
demonstrations with no absence case, so `copy_query_on_absence` fit every demo
and failed only on the query. The three-phase scheduler itself was sound, but its
`mixed` phase randomly chose zero or one match; therefore a six-pair window could
contain only one or even zero no-match examples.

The repair replaces that stochastic `mixed` phase with deterministic `absence`
and removes the unused random branch. The same historical lesson now produces
`[1, 2, 0, 1, 2, 0]`; when offset 5 is queried, offset 2 remains a sentinel demo.
A regression test requires at least two no-match examples in every checked
six-pair default lesson and failed on the old source before the implementation
change.

## Earlier repair context

Version 3.0 had already repaired the broader v2.1.2 restrictions: independently
placed candidates, equal-count nonmatching decoys, zero/one/multiple matches,
first-candidate precedence, translated unique matches, exact observable controls
and six canonical-fitting rivals. Its source-bound 300-lesson census remains
historical evidence for that source, not a measurement of v3.1. The retained
`counterexamples/current-shortcut.json` is likewise explicitly bound to the
v3.0 SHA and should not be read as current-source verification.

## Verification performed for v3.1

- Focused task suite: 39 tests passed. This includes the red/green absence
  regression and an exact-override test for aligned single matches.
- Semantic gate: 600/600 strict generated draws, 12/12 materialized lessons and
  72 cyclic rotations passed with zero declared-rival ambiguity or errors. All
  seven current rivals were source-bound and all five witness classes fired in
  every band.
- Cached adversarial scan: bands easy/medium/hard, seeds 0–63, starts 0–2,
  all six cyclic queries and all seven rivals. It covered 1,536 unique generated
  inputs, 576 lesson windows, 3,456 query rotations and 24,192 rival evaluations
  with zero schedule failures, validator failures or ambiguities.
- Selected Racket: six repaired seed-14 lesson pairs plus one dense side-6
  boundary input. All seven outputs agreed with the independent whole-grid
  authoring oracle; the no-match rival was refuted on both repaired absence pairs
  and the dense boundary case. Executed rule hash remained `cc8c5c7301a4`.

Reusable evidence tooling is under `checks/absence-sentinel-repair/`: `scan.py`
accepts an explicit `--seeds` bound and caches overlapping windows;
`prepare_racket.py` and `verify_racket.py` materialize and verify the compact
Racket witness set.

## Limits and failed attempts

A first uncached 256-seed scan exceeded the command timeout. The optimized cached
scanner was completed at 64 seeds; no 256-seed pass is claimed. An optional
semantic-gate run with `--enumerate-schedule-period` failed because this generator
does not declare `LESSON_SCHEDULE_PERIOD`; the required rotation gate then passed
without that unsupported option. The explicit scanner enumerates starts 0–2.

The checks cover seven plausible finite rivals, not all possible conditional
rules or downstream learner behavior. No model training, hidden-query scoring,
catalog approval or training admission was performed. The next useful action,
if greater assurance is required, is to run the cached scanner at a larger seed
bound under a deliberately larger timeout; no further generator change is
currently indicated.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f6e5bf65a749ee79:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ffbe31ada4158793dd6e1326c0066e599b9c7178bc9bec8e1b5637c878f02278`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source-bound repair explicitly addresses this finding; focused checks and Racket parity are reviewer-reported, not a new owner battery. Current task notes and retained integration record specify scope and finite limitations.

### Assessment or prior finding

## 312fb4bdff00

**Classification: reproduced teaching defect; no source edit made.** The audited generator SHA-256 is `ffbe31ada4158793dd6e1326c0066e599b9c7178bc9bec8e1b5637c878f02278`, with rule hash `cc8c5c7301a4`.

An ordinary easy-band lesson at `seed=14`, start index `0`, contains five demonstrations whose match counts are `[1, 2, 1, 1, 2]`, followed by a query with zero matches. A plausible rival performs the intended ordered D4 matching and returns the first matching candidate whenever one exists, but on absence returns a target-colored copy of the query instead of the authority's `[[0]]` sentinel.

The rival fits all five authoritative demonstrations. On the no-match query, the selected authority returns `[[0]]`, while the rival returns a 4×4 copy-shaped output. All inputs pass the validator and come from ordinary defaults. The existing finite semantic probe samples absence but does not guarantee that an absence case appears among the demonstrations, so this fallback remains teachable in some windows.

Evidence:

- Exact lesson and rival: `checks/audit/312fb4bdff00/finding.json`
- Materialized lesson: `checks/audit/312fb4bdff00/lesson-easy-14.json`
- Selected-Racket inputs and receipt: `checks/audit/312fb4bdff00/inputs.json`, `checks/audit/312fb4bdff00/racket.json`
- Seed/index scan: `checks/audit/312fb4bdff00/rival-scan.json` — seeds 0..255, starts 0..2, all bands; 225 ambiguous windows among 2,304 (75 per band)
- Existing portable tests and declared semantic gate: `checks/audit/312fb4bdff00-combined/result.json` — 35/35 tests plus the semantic gate passed, again isolating an undeclared teaching rival rather than an authority failure

Suggested repair for that generator: guarantee at least one no-match demonstration whenever the query may be no-match, or declare/test the wrong-absence-fallback rival and resample ambiguous windows.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-f6e5bf65a749ee79-v0001/audit_assets.json), manifest SHA-256 `c50dd0dc479044ebecb48d1fc9c4fc78c30c765ee44f1bae4585d98d9a7f4edb`.
<!-- arcpuzzles-current-audit-assessment:end -->
