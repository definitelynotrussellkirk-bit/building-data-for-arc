# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Complete-lesson shortcut probe

`lesson_probe.py` checks the task's pinned per-band lesson schedule against
**every** rule in `LESSON_COMPETITORS`. It reports rival survival by band,
hook disagreements, replay tuples, and the exact generator/rule hashes.

Run it from a prepared portable runtime. Fast mirror-backed census:

```bash
cd <packet>/checks/portable-runtime-after
PYTHONPATH=. python3 \
  <packet>/repo/generators/8c6fbfbe20d4/workspace/lesson_probe.py \
  --mode mirror --lessons-per-band 100 \
  --out <packet>/checks/lesson-probe.json
```

Canonical Racket-backed census (slower, production materialization path):

```bash
cd <packet>/checks/portable-runtime-after
PYTHONPATH=. python3 \
  <packet>/repo/generators/8c6fbfbe20d4/workspace/lesson_probe.py \
  --mode racket --lessons-per-band 100 \
  --out <packet>/checks/lesson-probe-racket.json
```

Exit code 0 means every declared competitor was refuted by every complete
lesson and `lesson_identifiable` agreed. Any surviving shortcut returns 1 and
is recorded with a replay tuple.
