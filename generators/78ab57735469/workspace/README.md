# Workspace

The selected implementation is `../generator.py`; workspace tools are
source-bound diagnostics and are never selected as the generator.

- `probe_schedule.py` iterates the generator's live `CANONICAL_SHORTCUTS` and
  `LESSON_COMPETITORS`, verifies canonical-shortcut fit, and checks consecutive
  lesson starts at every query position. Generated labels use the independent
  Python `rule_mirror`; use the shared Racket-labelled semantic gate and lesson
  census for authority evidence.

Run from the repository root:

```bash
python3 generators/78ab57735469/workspace/probe_schedule.py \
  --seed 0 --starts 16 --bands easy medium hard \
  --out ../checks/schedule-probe-final.json
```
