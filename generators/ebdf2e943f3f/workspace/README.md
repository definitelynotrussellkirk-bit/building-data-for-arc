# Shortcut and lesson probe

`shortcut_probe.py` is a source-bound regression tool for this generator. It discovers the generator's actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`; verifies canonical shortcut fit; finds exact generated counterexamples; and checks every query rotation for every requested cyclic start.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/ebdf2e943f3f/workspace/shortcut_probe.py \
  --seeds 8 --starts 16 --out ../checks/shortcut-probe.json
```

The task-local probe uses `rule_mirror` labels for fast deterministic diagnostics. The selected Racket rule remains authoritative, so retain the public battery and `lesson-census --rotate-query` reports beside the probe before making final claims.
