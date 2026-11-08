# Reusable review probes

The selected implementation is `../generator.py`; workspace tools are diagnostics and are never selected as generators. Tests use the portable reviewer-support helpers, so they work in both the source repository and staged runtime. Commands below run from an extracted review packet root; payload paths are relative to `repo`. Choose new evidence paths on reruns.

## Conflict and validator census

```bash
python3 run_with_racket.py python3 generators/57488f2a7c15/workspace/conflict_census.py --seeds 10000 --out ../checks/new-conflicts.json
```

Scans seeds 0..9999 with sample index equal to seed in each band, no overrides. It independently checks pixels, validator behavior and uniqueness, binds source/dependency/rule hashes, detects source drift, and retains concrete witnesses. Use `--expect-violations` only for an explicitly expected-failure diagnostic; exit zero in that mode does not mean the distribution passed. Actual Racket labels are obtained for retained violating witnesses.

## Exhaustive schedule profile audit

```bash
python3 run_with_racket.py python3 generators/57488f2a7c15/workspace/schedule_contract.py --out ../checks/new-schedule-profile.json
```

Checks all 18 cyclic starts and finite context-rival profiles, including arbitrary-holdout diagnostics and the explicit support/count limitation. It generates zero grids and executes zero Racket labels. `../tests/test_schedule_profiles.py` checks realized pixel features; the production lesson census supplies actual labels. The rejected synthetic 12-profile proposal is an intentional schedule diagnostic, not a failed model solve.

## Saved-label shorter-lesson diagnostic

```bash
python3 run_with_racket.py python3 generators/57488f2a7c15/workspace/short_lesson_probe.py --census ../checks/lesson-census.json --out ../checks/new-short-prefixes.json
```

Reuses each source-bound five-demo lesson's first N pairs as demonstrations and pair N as query, for N=3 and 4. It loads the actual rival declarations, deduplicates aliases by callable identity, counts both query ambiguities and unrefuted rivals, and saves an exact witness when one exists. It performs no new generation or Racket labelling and must not be described as a fresh public API invocation. Final review: three-demo prefixes 147/300 ambiguous; four-demo prefixes 0/300 ambiguous with all rivals refuted. Five remains the conservative declared contract, not an established minimum.

## Full task checks and production census

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 57488f2a7c15 --stage task_tests --timeout 600 --phase after --out ../checks/new-task-tests
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 57488f2a7c15 --per-band 100 --train 5 --test 1 --period 18 --rotate-query --rotation-policy diagnostic --timeout 1800 --out ../checks/new-lessons.json
```

The declared lesson contract uses five consecutive ordinary samples with no overrides. Set `--train 5` / `n_train=5` explicitly in public generate/export consumers that ignore `EXAMPLES_NEEDED`. Do not shuffle or rotate queries under this contract. `REGRESSION_PROBES.md` distinguishes baseline/intermediate/final evidence and describes the domain-law and exact-control tests.

If isolated pytest is missing despite a user-site install, use a proper venv. The review return includes `checks/bootstrap_test_env.py` for an offline setup from already-installed dependencies and `checks/replay_delta.py` for fresh-packet application and isolated regression replay. No environment is bundled.
