# Task-local qualification workspace

`qualification_probe.py` is a source-bound companion to the shared checks. It:

- checks every declared canonical shortcut against all canonical pairs;
- exercises every exact `grid_profile` override in every difficulty band;
- checks all four cyclic schedule starts and all four possible query rotations;
- samples per-band scene, canvas-profile, structural, deterministic, and witness coverage.

Run it from the repository root:

```bash
python3 generators/13507b4f7614/workspace/qualification_probe.py \
  --per-band 100 \
  --out ../checks/qualification-probe.json
```

The report is finite Python-mirror evidence. It does not replace the source-bound
Racket battery or `lesson-census --rotate-query` authority-labelled evidence.
