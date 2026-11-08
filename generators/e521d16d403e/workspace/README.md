# Reusable review tools — e521d16d403e

The selected implementation is `../generator.py` (reviewed version `4.1.0`).
Alternate sources and probes here are retained evidence and are never selected
automatically. These tools expose canonical answers or rule behavior; keep them
closed during visible-only solve episodes.

| Tool | Purpose and safeguards |
|---|---|
| `check_lesson_windows.py` | Materialize actual contiguous windows for every requested start, label unique inputs through the public batched Racket API, verify canonical-fitting declarations, and score all one-query rotations. It reads the generator's actual rival dictionaries and separates occurrences from unique inputs. |
| `find_lesson_counterexample.py` | Search a retained source for a complete ambiguous lesson and bind the result to public Racket labels and source hashes. |
| `override_probe.py` | Reproduce historical dimension/count/control defects with instrumentation and plain replay. |
| `semantic_probe.py` | Inventory candidate semantics, canonical-fitting rivals, and hand edge cases against public Racket outputs. |
| `lawful_minimal_probe.py` | Historical probe showing the executable Racket rule accepts lone symmetric objects. Current `self_check` intentionally narrows the selected curriculum to require a distractor. |
| `compact_evidence.py` | Deterministically gzip explicitly selected completed evidence and retain path/size/SHA restoration metadata. |
| `generator_v4_0_0.py` | Historical intermediate source that passed its then-declared rival set but retained a fixed second-largest-object shortcut. Never selected. |
| `parametric/prototype.py` | Proposed, unapproved episode-level `selection_metric` family (`occupied_cells` or `bbox_area`). Uses exact Racket labels, a canonical-source hash guard, public/private episode separation, and deterministic replay. |

## Reproduce current focused evidence

From the packet `WORK/` directory after `python3 setup_racket.py`:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check e521d16d403e \
  --stage task_tests --timeout 600 --phase after --out ../checks/replayed-tests

python3 run_with_racket.py python3 \
  generators/e521d16d403e/workspace/check_lesson_windows.py \
  --period 4 --seeds 0,1,17,37 --bands easy,medium,hard --train 3 --queries 1 \
  --out ../checks/replayed-windows.json

python3 run_with_racket.py python3 -m arcpuzzles lesson-census e521d16d403e \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/replayed-census.json

python3 run_with_racket.py python3 \
  generators/e521d16d403e/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/replayed
```

Output paths must be fresh. The window/census claims cover only declared rivals
and the stated seeds/sampler. Arbitrary explicit overrides do not inherit the
default curriculum claim.

## Current retained evidence

- final strict battery: `checks/after/`;
- portable task tests: `checks/task-tests/`;
- current cyclic windows: `checks/lesson-windows-after.json`;
- 300-lesson census: `checks/lesson-census-after.json`;
- parametric prototype: `checks/parametric/selection-metric-v1/`;
- exact bottommost witness: task `counterexamples/bottommost-lr-repair-witness.json`
  plus `checks/selected/bottommost-racket.json`.

Earlier logs and sources remain iteration history, not final evidence. The first
final-battery invocation was externally interrupted; `checks/after/result.json`
is the completed hash-verified resume and is the aggregate verdict.
