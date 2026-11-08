# Workspace

`reference_probe.py` is the retained independent geometry oracle and curriculum
probe for this task. It checks the repaired sampler without importing production
output helpers, verifies the strongest canonical-fitting rival, records the
fixed repeated-color counterexample, and audits 100 nonoverlapping lessons per
difficulty band by default.

Run from `repo/`:

```bash
python3 generators/d57b7deebba2/workspace/reference_probe.py \
  --lessons-per-band 100 --examples-needed 3 \
  --json-out ../checks/d57b7deebba2_lesson_probe.json
```

The selected generator remains `../generator.py`; workspace tooling is never
a label authority. The canonical Racket program is authoritative.
