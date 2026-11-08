# Workspace

The selected implementation is `../generator.py`; workspace files are not
automatically selected.

`semantic_probe.py` is a reusable source-bound lesson audit. It:

1. verifies every `CANONICAL_SHORTCUTS` function against every canonical pair;
2. assembles lessons from four consecutive production sample indices;
3. rotates all five deterministic schedule starts into the query slot;
4. tests every `LESSON_COMPETITORS` function against all three demonstrations
   and the query; and
5. writes the exact source hash, seeds, layouts, outcomes, unique-input count,
   and a concrete shortcut witness to JSON.

Example from the repository root:

```sh
PYTHONPATH=shared/runtime:. python3 \
  generators/515cca15a0b7/workspace/semantic_probe.py \
  --seeds 25 --out ../checks/cyclic-semantic-probe.json
```

The probe is finite evidence over declared rivals and the production schedule;
it is not proof against undeclared hypotheses.
