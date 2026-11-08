# Workspace for 9000d0ea6484

The selected implementation is `../generator.py`.

`reference_probe.py` is an independent task-local oracle and regression tool. It does not import the generator's rule mirror: it reconstructs aligned section signatures, applies an explicit priority order, enumerates all 24 section permutations, evaluates the canonical fixed-color shortcut, recovers advertised axes from pixels, and loads canonical pairs in source or portable-runtime layouts.

Run from `repo/`:

```text
PYTHONPATH=src:shared/runtime python3 \
  generators/9000d0ea6484/workspace/reference_probe.py \
  --per-band 300 --out ../checks/reference-probe.json
```

The report records the generator source hash, exact sampler recipe, unique-input count, self-check failures, non-unique orders, override round-trip failures, difficulty ranges, rival agreements, and canonical acceptance/oracle checks. It is Racket-free by design; use `arcpuzzles check`/`apply` separately for authority evidence.
