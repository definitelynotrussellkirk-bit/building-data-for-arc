# Task-local review tools

The selected implementation is `../generator.py`. Workspace files are not
selected generators. `review_probe.py` audits real generated inputs and canonical
Racket outputs in a fresh copied runtime, without mutating the source catalog.

## Replay from a full review packet

Run these commands from the packet root (the directory containing `WELCOME.md`).
The wrapper changes to `repo/` and supplies the pinned rootless Racket runtime.
Every output directory must be new; the tool refuses to overwrite evidence.

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 generators/c5f62271ea44/workspace/review_probe.py \
  --out ../checks/replay-current --tests
```

To measure the frozen assignment baseline with the same probe:

```sh
python3 run_with_racket.py python3 generators/c5f62271ea44/workspace/review_probe.py \
  --generator ../.review/baseline/repo/generators/c5f62271ea44/generator.py \
  --out ../checks/replay-baseline
```

The version 3.0.0 baseline is expected to exit 1, recording the position shortcut
and absent fragmented/extended support. Do not add `--tests` to this baseline
comparison unless intentionally demonstrating that the new regressions fail.

In an ordinary checkout with Racket available, run the script from the repo root
with a new output path. It derives the catalog root from its installed location;
keep it under this task's `workspace/` directory.

## What is checked

The default 128 seeds and eight positions produce 1,024 default observations.
The probe reports actual-Racket-derived transforms, four/eight-connected motif
component sizes, key spans, and joint grid/panel/palette/role counts. It fits one
transform per position on the first half of seeds and evaluates the second half.
It rejects a position with missing transform support or at least 50% held-out
fixed-transform accuracy. This deliberately catches severe concentration, not
all statistically detectable residual dependence.

It also checks all declared exact-axis combinations over all three difficulty
bands, all canonical pairs, four-demo lesson windows, and key-only interventions
that hold a panel fixed while asking the selected Racket rule for all eight
transforms. Coordinate transforms and role extraction are independent of the
generator's Python mirror; the mirror is checked, never used as label authority.

`report.json` records source/rule/probe hashes, counts, findings and bounded
exception examples. `examples.json` retains sixteen concrete labeled examples.
`process.json` records exit code, timeout and streams. `--tests` additionally
copies and runs the task-local test file, with a hash and results in `pytest.json`.
The task-local tests are run explicitly because the public repository suite does
not discover generator-home tests automatically.

Exit 0 means these implemented checks passed, not that an independent monitor
approved the generator or that a trained model improved. The seed split is not
a held-out task-family evaluation. Failed runs are intended to remain evidence.

## Public API smoke test

```sh
python3 run_with_racket.py python3 -m arcpuzzles generate c5f62271ea44 \
  --count 2 --seed 0 --train 4 --test 1 --difficulty medium \
  --allow-unapproved --out ../checks/replay-episodes.jsonl
```

`--allow-unapproved` is an explicit research choice. It does not grant approval;
emitted provenance must still say `approved: false`. Use four demonstrations,
not the current single-task command's default of three.
