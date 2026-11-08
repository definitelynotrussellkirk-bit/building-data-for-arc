# Top-k extension — proposed prototype

This task-local experiment keeps the original `3233860e2d81` reasoning pattern:
count every non-background color, rank colors by total frequency, and return the
highest-ranked colors as a one-column grid. It does **not** change the selected
canonical generator, rule hash, catalog status, or production interface.

## Parameter contract

| Parameter | Allowed values | Original setting | Executed effect |
|---|---:|---:|---|
| `top_k` | `2`, `3`, `4` | `3` | Number of highest-frequency colors returned |

The episode seed chooses one value once via `(2, 3, 4)[seed % 3]`. That exact
instantiated Racket program labels all three demonstrations and the query. Input
sampling uses an independent deterministic RNG, so changing only `top_k` leaves
the input family unchanged. Every input contains five colors with distinct
counts, so all three settings are lawful and produce visibly different output
heights.

`prototype.py` reads the selected canonical rule and changes only its single
`(build-grid 3 1 (r c) ...)` output-height site. For `top_k=3`, the instantiated
source is byte-for-byte identical to the canonical program. Every retained label
and counterfactual prediction is produced by the bundled Racket bridge; there is
no Python label mirror.

## Run

From `WORK/`:

```bash
python3 run_with_racket.py python3 generators/3233860e2d81/workspace/parametric/prototype.py \
  --seed 0 --out ../checks/parametric/top-k-s0
```

Use a new output directory for each run; the prototype refuses to overwrite old
evidence. Focused tests run through the task-test stage or directly with:

```bash
python3 run_with_racket.py python3 -m pytest -q \
  generators/3233860e2d81/tests/test_review_repair.py -p no:cacheprovider
```

## Public/private boundary

Only files under `public/` are solver-facing. Each contains three labeled
`train` pairs and one unlabeled `test` input, with no seed, parameter, program,
query answer, or expected output dimensions. `private/` retains exact Racket
text, hidden parameters, all labels, declared rival outputs, and query-rotation
checks. `report.json` is authoring evidence and must remain private.

The retained run covers three consecutive seeds, all three parameter settings,
two alternative-setting rivals per episode, and all four single-query rotations.
That finite evidence does not prove uniqueness against arbitrary rules, all
seeds, or broader input distributions, and it does not approve production
integration of the proposed extension.
