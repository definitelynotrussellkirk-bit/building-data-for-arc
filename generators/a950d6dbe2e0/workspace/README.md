# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Source-bound witness replay

From the extracted packet root, after installing the documented Python
requirements and running setup_racket.py:

```bash
python3 run_with_racket.py python3 generators/a950d6dbe2e0/workspace/probe_witnesses.py --out ../checks/witnesses-new
python3 run_with_racket.py python3 -m arcpuzzles check a950d6dbe2e0 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
python3 run_with_racket.py python3 -m arcpuzzles lesson-census a950d6dbe2e0 --per-band 100 --period 3 --rotate-query --timeout 1800 --out ../checks/lesson-census-new.json
```

Use new output paths. The witness tool checks all declared canonical shortcuts
against all canonical pairs, then checks six generated cases through the public
Racket API. It does not hardcode the rival-name list. Its report preserves each
input, actual output, rival output, seed, sample index and exact controls.

The default lesson guarantee is for three consecutive demonstrations plus one
query without exact overrides. The census records all cyclic start residues and
all held-out rotations; repeated rotations share the same four labelled pairs.
The tests independently exercise control and teaching behavior. Never use these
authoring helpers during a visible-only solve because canonical answers are read.
