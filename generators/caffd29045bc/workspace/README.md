# caffd29045bc reviewer workspace

Run the source-bound rival probe from the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/caffd29045bc/workspace/reference_probe.py \
  --seed 5000 --windows 16 \
  --out generators/caffd29045bc/counterexamples/four-shortcuts.json
```

The probe imports the generator by file path, iterates the generator's actual
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` declarations, verifies that each
rival fits all canonical labels, emits an exact generated counterexample for
each rival, and checks every query rotation in each requested period-four
window. Its report records generator/rule hashes, replay seed and sample index,
inputs, intended outputs, rival outputs, cell differences, and schedule results.
It is a finite declared-rival audit, not a universal uniqueness proof.
