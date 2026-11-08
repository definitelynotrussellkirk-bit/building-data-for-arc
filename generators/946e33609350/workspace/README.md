# Workspace

`lesson_probe.py` is a fast, source-hashed authoring check for the selected
three-profile lesson schedule. It tests ordered lessons, every query rotation,
profile-window coverage, and every rival declared by the adjacent generator.

Run from the packet root with:

```bash
PYTHONPATH=WORK/repo/shared/runtime python3 \
  WORK/repo/generators/946e33609350/workspace/lesson_probe.py \
  --starts-per-band 25 --seed 2468 --out WORK/checks/lesson-probe.json
```

This probe uses the Python rule mirror. Authoritative labels and final semantic
claims must still use the packet's Racket-backed check and lesson-census tools.
Workspace files are never automatically selected as production code.
