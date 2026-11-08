# Workspace

The selected implementation is `../generator.py`. Workspace artifacts are not
automatically selected.

`lesson_probe.py` is a reusable, source-bound curriculum census. It loads the
selected generator by path, samples the generator's actual four-example sliding
schedule, iterates its declared `LESSON_COMPETITORS`, and records source hash,
seed/index policy, domain limits, unique-input counts, override coverage, and
per-rival disagreements. Run it from `repo` with:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/7213d98ef029/workspace/lesson_probe.py \
  --lessons-per-band 100 --seed-base 72130 \
  --out ../checks/lesson-probe.json
```
