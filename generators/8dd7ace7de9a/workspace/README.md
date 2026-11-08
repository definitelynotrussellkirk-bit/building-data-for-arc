# Workspace tools

The selected implementation is `../generator.py`. These tools are retained for independent review and are never selected as generators.

## `reference_probe.py`

A separately written mirror of the canonical lexicographic period search. It also reads canonical pairs and selected authority files, computes the normalized rule hash, recovers all observable axes, and loads an explicitly named generator source. It intentionally does not import implementation helpers from `generator.py`.

## `lesson_probe.py`

A deterministic source-bound lesson census. It mirrors the inherited semantic gate's seed formula and sample-index stride, generates `EXAMPLES_NEEDED` demos plus one query, dynamically iterates the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks canonical shortcut fit, all cyclic schedule starts, witness supply, rival survival, uniqueness, and observed domain limits.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/8dd7ace7de9a/workspace/lesson_probe.py \
  --generator generators/8dd7ace7de9a/generator.py \
  --lessons-per-band 100 \
  --out ../checks/lesson-probe-final.json
```

The command exits nonzero if any declared shortcut fails its canonical-fit claim, any lesson is unidentifiable, any competitor survives all demos, any witness is absent, or the independent rule mirror disagrees.
