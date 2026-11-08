# Workspace

The selected implementation is `../generator.py`.

`curriculum_probe.py` is a fast, reusable Python-side check for every cyclic
three-demo lesson start. It reads the generator's live `LESSON_COMPETITORS`
registry, reports any surviving rival, and records profile/unique-input counts:

```bash
cd repo
PYTHONPATH=shared/runtime python3 generators/cf09cffb4663/workspace/curriculum_probe.py \
  --starts 18 --out ../checks/cyclic-curriculum-probe.json
```

It uses `rule_mirror`, so it complements rather than replaces the Racket-backed
semantic gate and lesson census.
