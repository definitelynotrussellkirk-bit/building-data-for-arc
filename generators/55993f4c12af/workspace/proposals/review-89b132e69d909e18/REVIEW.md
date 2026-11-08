Task `55993f4c12af`, generator `3.0.1`; final generator SHA-256 `1d38b983e4c7edb9d70d6bfec9877d5b631e4583a1398b8c8383a1d7f0a9a348`.
Baseline defect: the public API accepted invalid scalar seeds/sample indexes, including booleans, floats, strings, and negative indexes.
Repair: added strict pre-draw validation and 11 failing-first regression cases; no canonical sampling or rule behavior changed.
Parametric proposal: separate `operation ∈ {xor,and,or}` × `output_color ∈ 1..9` episode harness, canonical default `or/4`.
Final canonical battery: 12/12 stages green; task-local portable tests: 112/112 green.
Lesson evidence: three demonstrations plus one query, ordered production schedule; 300/300 lessons and all 1,200 query rotations had no declared-rival ambiguity.
Parametric evidence: 27/27 settings completed, five canonical pairs matched, and one lawful witness produced 27 distinct outputs.
Post-repair solve: 3/3 visible examples passed; earlier rule exposure declared yes, no source/reference consultation during the solve.
Racket authority: unchanged; `RULE_HASH` remains `ce2dee847896` and authority synchronization stays green.
Remaining limitation: all rival and parameter evidence is finite; the proposed variants are not production-approved.
Fresh replay: exact patch applied to all 90,295 original files; clean-checkout focused tests passed 112/112.
Acceptance: routine.

# Detailed review

## Finding table

| ID | Affected path | Finding / repair | Evidence | Status |
|---|---|---|---|---|
| R1 | `generators/55993f4c12af/generator.py` | Invalid scalar call arguments reached `gen_ctx`; added exact `type(...) is int` checks for `seed`/`sample_index` and rejected negative indexes before any draw. | `checks/before/checks/55993f4c12af_before_defect_lint.log`; `checks/after/checks/55993f4c12af_after_defect_lint.log` | Fixed; before battery 11/12, after battery 12/12. |
| R2 | `generators/55993f4c12af/tests/test_generator.py` | Added 11 regression cases for bool/float/string seeds and bool/float/string/negative sample indexes. | `checks/task-tests/result.json` | 112/112 portable task tests pass. |
| P1 | `workspace/parametric/` and `tests/test_parametric_extension.py` | Built a separate finite Racket-backed rule-parameter prototype with complete private/public episodes, canonical parity, demo-only rival checking, and an honest ambiguity diagnostic. | `checks/parametric/run-01/report.json`; `checks/parametric/run-01/ambiguity.json` | Proposed only; 27/27 settings pass the retained audit. |
| L1 | production lesson sampler | Rechecked teaching quality after the API repair against all declared rivals and every query rotation in the materialized bundles. | `checks/lesson-census.summary.json` | 0/300 production ambiguities; 0/1,200 rotation ambiguities; 1,200 unique inputs. |
| S1 | `solve/` | Fresh visible-example implementation independently recovered stacked-panel occupancy OR. | `solve/summary.json`; `solve/FINISHED_NOTES.md` | 3/3 visible examples pass; final attempt recorded. |

## Canonical repair

The baseline generator source was already semantically strong but failed the newly
strict scalar-contract detector with 33 findings. The root cause was local and
reproducible: `_validate_call` checked difficulty and overrides but delegated
`seed` and `sample_index` directly to a permissive context layer that accepts
Python values equal to integers, notably booleans and integral floats. A negative
sample index also entered the cyclic schedule. The repair validates both arguments
before `gen_ctx` and before schedule selection. It deliberately does not coerce
values, preserving an exact and falsifiable public API.

The focused regressions were written and observed failing first (11 failures),
then passed after the one validation change. The pre-existing 52 target tests plus
those 11 canonical tests remained green. The portable task-test stage additionally
runs the 49 parametric tests, for 112 total passing tests.

## Required checks

- Before battery: 11 green stages, one failure (`defect_lint`) at generator SHA
  `f5bc92f43afad9f059e3e88e54a89e4bb12f5c246cd9d2729edaeae0933ed722`.
- After battery: 12/12 green at generator SHA
  `1d38b983e4c7edb9d70d6bfec9877d5b631e4583a1398b8c8383a1d7f0a9a348`.
- Portable selected tests: 112 passed, 0 failed, 0 skipped.
- Production/rotation census: 300 materialized lessons, 1,200 labeled pairs,
  1,200 unique inputs, 1,200 held-out-query rotations, no materialization or
  scoring errors, and no declared-rival ambiguities.
- Exhaustive task-local schedule probe: 25 cycles per band × four starts = 300
  cyclic lesson windows, with zero declared-rival ambiguities.
- Fresh return replay: full original packet extracted (90,295 files), patch check
  and application exited 0, final generator hash matched, and 112/112 focused
  tests passed in the replayed checkout.

The lesson census uses three demonstrations and one query. Production ordering is
the generator's four-slot cyclic schedule; the retained census also holds out each
of the four materialized pairs once while preserving the order of the remaining
three. This verifies the actual production assembly and all rotations of those
300 finite bundles, not every possible seed or every conceivable rival.

## Parametric-rule assessment

A small, reasoning-preserving parameterization is suitable as a proposal:

- `operation`: `xor`, `and`, or `or` over aligned nonzero occupancy;
- `output_color`: any ARC foreground color `1..9`;
- canonical/default: `or` with color `4`.

The prototype selects one parameter setting once per episode using a versioned
SHA-256 domain, then applies one exact Racket lambda to three demonstrations and
one query. Ordinary inputs retain all four truth-table relations (`00`, `10`,
`01`, `11`), so the demonstrations distinguish all 27 declared settings. The
all-settings audit completed 27/27 episodes, matched all five canonical labeled
pairs under the default, and retained a lawful witness with 27 distinct outputs.
`ambiguity.json` deliberately removes distinguishing states and correctly leaves
both `and/3` and `or/3` alive; this is a checker canary, not trainable output.

The proposal remains separate from `generate()` and the canonical `RULE_HASH`.
It is finite evidence, not variant approval, exhaustive seed coverage, or a claim
that the 27 rivals span all plausible ARC hypotheses.

## Self-review for introduced shortcuts

The canonical change only rejects malformed API calls, so it does not narrow the
accepted grid distribution or alter labels. The parametric proposal could invite
operation-name memorization if hidden metadata leaked; its public export therefore
contains only demonstrations and query inputs, and the tests verify that settings,
seeds, programs, and query labels are absent.

## Scope

Only the selected task's generator, task-local tests, notes, and
`workspace/parametric/` proposal were changed. Audit targets were inspected but
left untouched. No approval or training-admission state was changed.
