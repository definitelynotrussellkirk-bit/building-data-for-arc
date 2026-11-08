# Review workspace

`review_probe.py` is a replayable, task-local diagnostic for future generator
reviews.  It does not replace the packet's Racket-backed label checks.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/e3c21120e3d1/workspace/review_probe.py \
  --seeds-per-case 2 \
  --lesson-starts 16 \
  --out ../checks/review-probe.json
```

The probe:

- replays every labeled canonical pair;
- enumerates every exact Cartesian combination of declared integer axes in
  `None`, `easy`, `medium`, and `hard` bands;
- checks exact observability, deterministic fresh output, global RNG purity,
  `self_check`, and collisions with the generator's current competitors; and
- builds complete lessons at cyclic schedule starts, rotating each example into
  the query slot and calling `lesson_identifiable`.

A nonzero exit means at least one reproducible finding is recorded in the JSON.
The result is finite and mirror-based: always run `arcpuzzles check ...` with
Racket before accepting labels, and remember that undeclared hypotheses are
outside this probe's search space.
