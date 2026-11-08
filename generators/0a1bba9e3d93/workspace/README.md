# Review workspace for 0a1bba9e3d93

The selected implementation is `../generator.py`.

- `reference_probe.py` is an independent Python transcription of the canonical bbox-relative delta rule plus structural facts. It deliberately does not import implementation helpers from the selected generator.
- `lesson_probe.py` emulates production four-demo/one-query assembly, sequential sample indices, retry and duplicate rejection, declared rivals, canonical-shortcut fit, and all cyclic starts of the four-position schedule.
- `lesson_census_100.json` is the final source-bound report for seeds 0–99 in each difficulty band. It records source hashes, runner policy, exact denominators, unique inputs, profile sequences, rejection reasons, and rival survivor counts.

Reproduce from `repo/`:

```bash
python3 generators/0a1bba9e3d93/workspace/lesson_probe.py \
  --lessons-per-band 100 --seed-start 0 \
  --out generators/0a1bba9e3d93/workspace/lesson_census_100.json
```

Workspace drafts are not selected automatically.
