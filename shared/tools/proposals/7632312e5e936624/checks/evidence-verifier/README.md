# Lesson-evidence verifier implementation evidence

## Deliverables

- `WORK/repo/generators/9b37d4bbfb7e/workspace/verify_lesson_evidence.py`
  - SHA-256: `07d1ac11da3b146c9b39c230b38d0bc486fac42cebd72a2652023b967a46c49d`
- `WORK/repo/generators/9b37d4bbfb7e/tests/test_verify_lesson_evidence.py`
  - SHA-256: `55b767232eb7ce2107f75662bf8dee8580c6a58c1394cd7bd3160e803d3d15da`
- Final receipt: `WORK/checks/final/lesson-evidence.json`
  - SHA-256: `bec0f567f9e788ab904bca3b096fae24ac49fccd96f307b26e88007b051316f0`

The current generator was not edited by this work. Its final receipt is bound
to source SHA-256
`721dd5dac679d41722e20f174628c892f06cc61f91f109dae2040b5e0335e044`.

## Implementation contract

The CLI uses only the standard library and accepts portable source/report/output
paths. It reads generator metadata with AST without importing or executing the
generator. It derives rival names from the reports, with no hardcoded rival list.

It checks task/source/rule-pin bindings; matching reported rule source/callable
hashes; manifest source and rule-record bindings; materialization and scoring
status; aggregate and nested error, ambiguity, and warning fields; report
summaries against actual lesson records; instance/input hashes; complete accepted
pair traces; and every query holdout. Fixed-seed enumeration must cover every
declared band and every source-declared starting residue. The report's independent
modulo-six diagnostic counter is not confused with the declared period four.

The policy is conservative: every reported rival score must be refuted, provider
search must not be truncated, and rejected-pair schedules are not accepted by this
receipt contract. Unknown required formats or inconsistent/missing required data
produce a JSON rejection and nonzero exit. An explicitly requested output file
is replaced with that rejection receipt so a previous success cannot linger.
Input source/report files cannot be used as the output destination.

Every receipt keeps `global_approval: false` and the unresolved shared
`declared_period_not_enumerated` warning. It does not execute Racket, rehash the
Racket artifacts independently, rerun scoring, change catalog state, or establish
identifiability outside the finite reported evidence.

## Test-driven evidence

1. `test_verify_lesson_evidence.initial.py` preserves the initial test source.
2. `red-test.log`: the first valid-pair test failed because the new CLI did not
   exist. Exit 1; one failing test, 53 deselected.
3. Initial implementation: all 54 new tests passed.
4. `red-boolean-index.log`: an additional adversarial test exposed Python's
   container equality treating boolean `true` as integer index `1`. Exit 1;
   one failing test, 54 deselected. Recursive type-strict equality fixed it.
5. `green-tests.log`: the complete task-local test directory passed, **188 tests**,
   exit 0. This includes **55 new verifier tests** and the existing task tests.
6. `final-command.log`: the final CLI accepted the final report pair, exit 0.

## Verified receipt counts

| Evidence | Lessons | Labelled pairs | Required query rotations | Unique input grids |
| --- | ---: | ---: | ---: | ---: |
| Random census | 300 | 1500 | 1500 | 1500 |
| Fixed-seed declared-period census | 12 | 60 | 60 | 9 |

The receipt covers 27 declared rival entries, easy/medium/hard bands, four
demonstrations plus one query, declared period 4, fixed seed 0, starting residues
0-3, and query positions 0-4. Zero-error claims were reconciled with detailed
lesson/rotation records rather than copied from aggregate status strings.

## Exact final commands

Launch cwd for both commands:
`/workspace/scratch/b924d53d1914/packet/WORK`.
The wrapper reports effective cwd `WORK/repo`.

```sh
.venv-review/bin/python ../review.py run /workspace/scratch/b924d53d1914/packet/WORK/.venv-review/bin/python -m pytest -q generators/9b37d4bbfb7e/tests
```

Exit 0, 188 passed in 6.88 seconds.

```sh
.venv-review/bin/python ../review.py run /workspace/scratch/b924d53d1914/packet/WORK/.venv-review/bin/python generators/9b37d4bbfb7e/workspace/verify_lesson_evidence.py --generator generators/9b37d4bbfb7e/generator.py --random-census /workspace/scratch/b924d53d1914/packet/WORK/checks/final/lesson-census.json --schedule-census /workspace/scratch/b924d53d1914/packet/WORK/checks/final/schedule-census.json --output /workspace/scratch/b924d53d1914/packet/WORK/checks/final/lesson-evidence.json
```

Exit 0, status `evidence_verified`. Both reports are bound to the current
generator hash; the intermediate hash-21e reports were not used for this receipt.
