# Workspace

`probe_curriculum.py` is the fast exhaustive companion to the shared
Racket-scored lesson census. It checks every single-pair query rotation of every
four-pair cyclic window over requested starts, seeds, and difficulty bands,
iterating the generator's current `LESSON_COMPETITORS` declarations rather than
duplicating a rival-name list.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/f891d1ff5dd8/workspace/probe_curriculum.py \
  --seeds 0,17,20,91 --starts 64 \
  --out ../checks/curriculum-probe-final.json
```

The retained run covers 4,096 rotations and is bound to generator SHA-256
`633291826a9a5fe45eacbd918bef677a5864e4722525ced0e56cf65176cead27`.
This probe uses `rule_mirror` for speed; `checks/lesson-census.json` is the
source-bound Racket-labelled evidence.

`parametric/prototype.py` is a separate proposed/unapproved extension for the
hidden episode-level parameter `cycle_direction = forward | reverse`. Its exact
Racket evidence and public/private leakage checks are retained under
`checks/parametric/cycle-direction-final/`.
