# Workspace

The selected implementation is `../generator.py`; workspace tools are diagnostics and are never automatically selected.

## `probe_curriculum.py`

This fast source-bound probe fills the one coverage gap called out by the shared lesson census: it checks **every cyclic four-demo start** and rotates **all four corner codes into query position**. It discovers `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `CANONICAL_SHORTCUTS` from the generator rather than copying rival names. It also validates all canonical pairs and 24 exact boundary-override cases.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime:src python3 \
  generators/c5c5f3f84f12/workspace/probe_curriculum.py \
  --seeds-per-band 8 \
  --out ../checks/curriculum-probe.json
```

A passing report is deterministic and JSON-safe. It uses the task-local independent Python oracle for speed; the focused regression and full battery remain the Racket-parity authorities.
