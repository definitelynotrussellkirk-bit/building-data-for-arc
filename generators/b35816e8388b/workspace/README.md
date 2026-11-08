# Workspace

`lesson_probe.py` is the retained source-bound curriculum census for the selected implementation in `../generator.py`. It imports the generator's live `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and witness declarations, verifies each canonical-shortcut claim against all canonical pairs, and checks every cyclic schedule start over at least 100 lessons per band.

From the packet root:

```sh
PYTHONPATH=repo/shared/runtime python3 \
  repo/generators/b35816e8388b/workspace/lesson_probe.py \
  --lessons-per-band 120 \
  --out checks/lesson-probe-final.json
```

The probe uses three consecutive demonstrations plus the next query with a shared lesson seed. It is a finite census of this sampler, not a proof of universal induction. Final evidence is retained in `checks/lesson-probe-final.json` and `checks/lesson-probe-final.log`.
