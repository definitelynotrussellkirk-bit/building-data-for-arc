# Workspace

`reference_probe.py` is an independent, portable pixel-level oracle for the
selected frame-pour task. It does not generate production labels. It checks all
canonical labels, validates ordinary draws, and compares the intended geometry
with the canonical-fitting `fixed_two_arms` rival.

From `WORK/repo`:

```sh
PYTHONPATH=shared/runtime python3 \
  generators/bee63e6e52bd/workspace/reference_probe.py \
  --count 64 --out ../checks/reference-probe.json
```

The probe locates canonical data with `reviewer_support.find_root(__file__)`, so
it also runs from the task-test portable runtime. Keep alternate drafts and
one-off experiments here; only `../generator.py` is selected automatically.
