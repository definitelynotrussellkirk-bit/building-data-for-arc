# Workspace

Workspace files are maintainer-facing probes and are not automatically selected as the generator implementation.

## `shortcut_probe.py`

Reproduces the canonical demonstration ambiguity and checks generated lesson identifiability against every declared rival.

Human-readable run:

```bash
PYTHONPATH=shared/runtime:src python3 \
  generators/e942ce41cbf5/workspace/shortcut_probe.py --seeds 12 --windows 6
```

Machine-readable run:

```bash
PYTHONPATH=shared/runtime:src python3 \
  generators/e942ce41cbf5/workspace/shortcut_probe.py --json --seeds 12 --windows 6
```

The default census checks 216 generated lessons (three bands × twelve seeds × six starting windows). It reports canonical shortcuts that fit every demonstration but change the canonical query, any generated lesson rejected by `lesson_identifiable`, and any declared rival that survives all demonstrations in a generated lesson.
