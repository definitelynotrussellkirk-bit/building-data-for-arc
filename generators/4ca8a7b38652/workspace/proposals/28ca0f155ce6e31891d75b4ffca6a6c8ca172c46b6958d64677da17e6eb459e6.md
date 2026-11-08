# Review `review-ad71de162668ae32`
Task: `4ca8a7b38652`; inherited version 3.0.0, valid sampling preserved.
Defect: boolean seeds/indices and negative sample indices were silently accepted.
Repair: require literal integer seeds and nonnegative integer indices; refresh stale notes/SUMMARY.
Final generator SHA-256: `d37aae7cb061aee2b45ba081dd7ce5c1811adc35aaac3b5ed57200aae0fd1aac`.
Checks: final strict battery 12/12 green; portable task tests 61/61; 64 valid baseline calls unchanged.
Canonical lessons: five demos + one query; 300/300 production lessons and 1,800/1,800 rotations pass declared rivals.
Schedule: all five starts at seed 0 × three bands; 15/15 lessons and 90/90 rotations pass.
Prototype: offsets −1/0/+1, 12 ordered episodes, 72 primary Racket labels, 108/108 wrong rivals refuted by demos; unapproved.
Limits: no local repair blocker; fresh replay + 61 tests + Racket CLI passed; wider suite retains 17 failures.
Reference: canonical and selected Racket authorities unchanged; proposal programs are separate.
Acceptance: needs attention — accept the narrow repair separately; decide on variants and route shared-suite/audit findings.

## Built and retained

The task patch includes a working episode generator, three exact Racket programs,
portable tests, a 64-request compatibility fingerprint and invalid-call
counterexamples. `workspace/parametric/README.md` gives runnable commands.
Only the assigned task's permitted source paths change. Shared tools, canonical
data, selected authority, audit sources and frozen fixtures are unchanged.
VERSION stays 3.0.0 to preserve valid RNG keys; the source hash identifies the fix.

The proposed rule preserves color counting and per-pixel enlargement with one
offset fixed for an entire episode. Offset zero replays all six canonical pairs.
The CLI supplies five ordered demonstrations, one 3×3 or 6×6 query, public
solver inputs and separate private labels/programs. Twelve saved episodes use
all three settings, both sizes and seeded selection. A same-input witness gives
output sides 3, 6 and 9. The suite executed 297 Racket calls: 72 primary labels,
216 parameter-rival labels, six canonical parity checks and three witness labels.
Named shortcut rivals are Python hypotheses. All 108 wrong-rival/episode
combinations are refuted by demonstrations; all 12 chosen rules survive.
Evidence: `checks/parametric/final-suite/SUMMARY.json`,
`checks/parametric/REPLAY.json`, `checks/parametric/COMMANDS.json`, and
`checks/canonical-review/PROTOTYPE_REVIEW.md`.

## Findings and patch status

| ID | Task / path | Evidence | Patch status | Test result |
| --- | --- | --- | --- | --- |
| R1 | `4ca8a7b38652/generator.py` request scalars | `checks/scalars/` | Repaired; valid draws preserved | 30 red failures become green; all 61 task tests pass |
| P1 | `4ca8a7b38652/workspace/parametric/` | `checks/parametric/final-suite/SUMMARY.json` | Runnable proposal; unapproved | 20 prototype tests pass; 12 ordered episodes distinguish settings |
| eb46-A1 | `eb46daa8881c` exact color controls | `checks/audit/eb46daa8881c/probe.json` | Finding only; source unchanged | Reproduced ignored requests; audit preset fails missing tests/contracts |
| eb46-A2 | `eb46daa8881c` clean-diagonal rival | `checks/audit/eb46daa8881c/racket.json` | Finding only; source unchanged | Validator accepts 5×5 witness; Racket and rival differ |
| 0a44-A2 | `0a444f80387e` crop teaching | `checks/audit/0a444f80387e/ambiguous_lesson.json` | Finding only; source unchanged | 8/100 medium lessons ambiguous; exact query verified in Racket |
| S1 | Wider repository suite | `checks/repository-suite/triage.json` | Outside permitted patch | 1,002 passed, 17 failed, 3 skipped |

## Evidence determining the canonical verdict

| Check | Actual result | Evidence |
| --- | --- | --- |
| Baseline battery | 11/12 green; 15 request-validation warnings | `checks/before/result.json` |
| New scalar regressions before repair | 30 failed, 1 passed | `checks/scalars/red.log` |
| Scalar plus inherited tests after repair | 41 passed | `checks/scalars/green.log` |
| First strict after battery | 11/12 green; schedule receipt missing | `checks/after/result.json` |
| Final strict after battery, receipt attached | 12/12 green; zero warnings/failures | `checks/after-final/checks/4ca8a7b38652_after_battery_summary.json` |
| Portable task-local suite | 61 passed; zero failures/errors/skips | `checks/task-tests/result.json` |
| Strict inputs / canonical acceptance | 600/600 generated; 6/6 canonical | final battery receipts |
| Exact overrides | 1,080/1,080 accepted; unknown key rejected | final override receipt |
| Profile floor | 47/60 exact and envelope hits; easy 17, medium 16, hard 14 | final profile-floor receipt |
| Production census | 300 lessons, 1,800 pairs, 1,656 unique inputs; zero ambiguity | `checks/lesson-census.summary.json` and `.json.gz` |
| Query rotations | 1,800 tested; zero ambiguity/warnings/errors | same census |
| Declared schedule | 15 lessons, 90 pairs, 27 unique inputs, 90 rotations; zero ambiguity | `checks/schedule-census.summary.json` and `.json` |

Canonical lessons use five demonstrations and one query, with every single
holdout tested against five unique declared rival functions (eleven aliases).
Schedule enumeration exhausts five starts at one seed across three bands; it is
not an all-seed proof. Prototype query rotation is unknown: its tested policy
is ordered. Finite rival checks do not establish a unique rule among all
possible programs. Repeated inputs are not counted as independent evidence.

## Self-review, solves and audits

The repair acts before generation and changes only invalid-request handling;
64 saved valid requests, 24 additional override calls and unchanged RNG version
provide evidence against an accidental distribution restriction. The strongest
canonical-fitting rival remains “all colors minus one”: the ordinary zero-free
seed-0/index-1 witness yields 9×9 in Racket and 6×6 under the rival, and the
preserved schedule supplies this distinction.

The blind solve for `80f776fb3ce5` finished before task-source inspection: one
genuine attempt, 3/3 visible examples. The exposed post-repair solve for
`4ca8a7b38652` uses the final generator bytes: one genuine attempt, 5/5 visible
examples. Overall prior source exposure is declared for the latter; neither
solver consulted a reference during solving. Both masked-query correctness
verdicts remain unknown. Frozen finish records are in `solve-blind/` and `solve/`.

`AUDIT.md` preserves two independent findings without target edits:
`eb46daa8881c` ignores exact color-count controls and omits a shortcut distinction;
`0a444f80387e` leaves a component-only crop rival indistinguishable in 8/100
sampled medium lessons. Both audit presets also fail for missing tests and
semantic contracts; absence is not a pass.

The wider repository run completed with 1,002 passed, 17 failed, 3 skipped and
18 passed subtests. Its full log, JUnit XML and per-test triage are in
`checks/repository-suite/`. Triage identifies 13 environment-related failures,
two shared-tool assertion mismatches and two unrelated archival-task fixture
mismatches with unresolved causes. Twenty-five relevant artifacts match the
original ZIP byte-for-byte, but the original full suite was not rerun; this is
not a claim that baseline execution reproduced every failure. Shared failures
remain outside this permitted patch and do not make the repository green.

## Fresh return replay

The public replay helper extracted the declared task/runtime dependency closure:
347 of 99,608 original files. It initialized Git at the exact fresh WORK root,
applied the patch and verified all 12 changed files against this review, including
new files. The generator matches the final source hash. Source patch SHA-256:
`28ca0f155ce6e31891d75b4ffca6a6c8ca172c46b6958d64677da17e6eb459e6`.

A separately created fresh virtual environment installed NumPy 2.5.4, Pillow
13.0.0 and pytest 9.1.1. Focused tests passed 61/61 with no failures, errors or
skips (19.24 seconds). A real Racket-backed CLI episode at seed 23, offset +1,
query side 6 exited zero and reproduced both public and private files byte for
byte. This is a selected-task replay, not a second full-repository suite.

`checks/handoff/replay.json` deliberately retains the helper
`patch_replay_passed_tests_pending` status; subsequent results are separately
recorded in `checks/handoff/fresh-verification.json`, `fresh-tests.xml`,
`fresh-tests.log`, `fresh-environment.json` and `fresh-episode/`. The exact
actual fresh CWD is recorded there and as `actual_cwd` for the relative
`fresh_checkout/WORK` alias in RESULTS. The replayed patch and final authoring files remain identical, as recorded in
`checks/handoff/package-identity.json`. The final archive must carry that exact
source.patch digest in both its bytes and generated INTAKE; this is checked
after packaging. Report-only edits do not change the tested source delta.
