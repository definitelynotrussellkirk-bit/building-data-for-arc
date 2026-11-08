# Proposed `target_size` rule parameter

This directory is an isolated **prototype**. It does not change the selected
canonical generator, canonical Racket authority, approval state, or production
API.

The parameter is chosen once per episode:

| Value | Status | Transformation |
|---|---|---|
| `5` | proposed alternative | Recolour exactly five-cell objects red(2); all others blue(1). |
| `6` | canonical/default | Recolour exactly six-cell objects red(2); all others blue(1). |
| `7` | proposed alternative | Recolour exactly seven-cell objects red(2); all others blue(1). |

The reasoning invariant is unchanged: find same-colour 4-connected nonzero
objects and classify each by cardinality. Every pair contains objects of sizes
5, 6, and 7, plus a size-3 distractor, so every demonstration distinguishes all
three settings. Inputs are generated independently of the hidden setting.

The size-6 program is the exact canonical `program_solution` bytes. Every label
and opposite-setting prediction is executed by the packet's included Racket
bridge; no Python output mirror creates evidence.

From the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/d8d37830884c/workspace/parametric/target_size.py \
  evidence --seed 900 --out ../checks/parametric/target-size-900

python3 review.py run python3 -m pytest -q \
  generators/d8d37830884c/tests/test_parametric_target_size.py
```

The evidence directory contains exact Racket programs, three private complete
episodes, solver-safe public challenges, a shared-input differing witness, and a
hash/runtime report. This is finite authoring evidence for three values, not
training approval or universal identifiability against undeclared rules.
