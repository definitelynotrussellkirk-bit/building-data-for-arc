# Workspace

The selected implementation is `../generator.py`; workspace files are reviewer tools and are never selected automatically.

`probe_curriculum.py` imports the selected generator declarations directly and checks:

- all 64 lower/upper joint override boundary combinations;
- every four-profile cyclic start in all three difficulty bands;
- all 48 possible held-out query rotations; and
- every currently declared `LESSON_COMPETITORS` rule, without copying a rival-name list into the probe.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/f0f02eb1d2e0/workspace/probe_curriculum.py \
  --out ../checks/f0f02eb1d2e0-curriculum-probe.json
```
