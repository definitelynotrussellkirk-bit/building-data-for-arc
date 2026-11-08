# Source-bound review probes

These are authoring tools with access to canonical/reference labels. Do not
use them during a visible-only solve. All commands below run from the extracted
packet root; the wrapper changes the working directory to `repo`.

## Palette orders and declared rivals

```sh
python3 run_with_racket.py python3 generators/19e04051ad0d/workspace/color_cycle_probe.py --phase final --per-band 200 --out ../checks/color-cycle-final-replay.json
```

Enumerates the generator's actual CANONICAL_SHORTCUTS, LESSON_COMPETITORS and
SEMANTIC_RIVALS mappings, plus a separately implemented numeric-predecessor
probe. Reports canonical fits, unique inputs, all observed color-rank orders,
three-demo window survivors and an exact counterexample. Generated labels in
this diagnostic come from the Python mirror; canonical labels are stored
reference labels. Counts and source hashes prevent conflating baseline and
repaired evidence.

## Production lessons and every query rotation

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 19e04051ad0d --per-band 100 --period 2 --timeout 1800 --out ../checks/lesson-census-replay.json
python3 run_with_racket.py python3 generators/19e04051ad0d/workspace/cyclic_lesson_probe.py --census ../checks/lesson-census-replay.json --out ../checks/cyclic-query-replay.json
```

The second command requires the exact current generator hash, a completed
error-free census, and four materialized pairs per lesson. It verifies instance
hashes, regenerates the actual input sequence, compares the Python mirror with
materialized Racket labels, dynamically scores all declared rivals and checks
all four choices of query. Refusal on stale evidence is intentional. A sampler
that skips/reorders inputs fails the explicit consecutive replay comparison;
extend provenance handling rather than silently claiming equivalence.

## All finite joint controls

```sh
python3 run_with_racket.py python3 generators/19e04051ad0d/workspace/joint_axis_probe.py --out ../checks/joint-axes-replay.json
```

Exhausts heights 8..12, all fourteen layouts (including `222`), backgrounds
0..9, both schedule phases and three bands: 4,200 calls at seed 77199. Checks
strict validity, exact observable controls and that both numeric directions are
balanced for each joint control tuple. This is not exhaustive over random seeds
and is not an independent Racket evaluation.

All probes reject overwriting an evidence file. Use a new output path for each
run. Successful probes are evidence for their stated hypotheses and sample
plans, not training approval or proof against undeclared rivals.

## Regression tests

```sh
python3 run_with_racket.py python3 -m pytest -q generators/19e04051ad0d/tests
python3 run_with_racket.py python3 -m arcpuzzles check 19e04051ad0d --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-replay
```

The task-local suite contains 15 unique tests. The portable snapshot currently
runs seven of them again via a root fixture mapping (22 executions total).
Retained red-before and green-after logs demonstrate the shortcut regressions,
canonical declaration checks and malformed-lesson fix. Input distributions and
source bytes must be rechecked whenever the generator changes.
