# Workspace

`review_probe.py` is a source-bound diagnostic for the selected generator. It:

- verifies every declared `CANONICAL_SHORTCUTS` solver against all canonical pairs;
- probes every exact scene-profile override in every difficulty band;
- evaluates declared witnesses and rivals on those profiles;
- exhaustively rotates the query across short cyclic lesson windows; and
- reports input uniqueness over a configurable draw census.

Run from the packet root with the packet wrapper so `reviewer_support` is on the
path:

```bash
python3 run_with_racket.py python3 generators/192d2bc2de61/workspace/review_probe.py \
  --starts 16 --unique-draws 100 --out ../checks/review-probe.json
```

The probe uses an independent Python mirror for fast schedule diagnostics. It is
not label authority; the battery, `arcpuzzles apply`, and lesson census provide
the retained Racket-backed evidence.
