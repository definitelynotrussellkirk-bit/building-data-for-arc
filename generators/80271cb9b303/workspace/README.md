# Workspace

The selected implementation is `../generator.py`. This directory contains
source-bound review tools; it is not automatically selected at runtime.

## Curriculum probe

`curriculum_probe.py` checks the declared default period schedule (`4, 3,
5..6`), all three cyclic lesson starts, task `self_check`, lesson
identifiability, actual declared competitors, canonical-shortcut fit, unique
input counts, and slot histograms. It intentionally does **not** execute Racket;
the standard battery remains authoritative for rule parity.

From `repo/`:

```bash
python3 generators/80271cb9b303/workspace/curriculum_probe.py \
  --seeds 200 --seed-start 1000 --bands easy,medium,hard \
  --output ../checks/after-curriculum-probe.json
```

The default run covers 600 lesson cycles, 1,800 overlapping cyclic lesson
windows, and 3,600 generated grids. The JSON records the final generator hash,
exact seed/sample policy, denominators, and first counterexamples if any.
