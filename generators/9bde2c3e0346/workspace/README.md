# Review workspace: 9bde2c3e0346

`probe_bbox_frames.py` is a reusable, source-bound contract probe. From the
repository root with the portable runtime active, run:

```bash
python3 generators/9bde2c3e0346/workspace/probe_bbox_frames.py \
  --out ../checks/bbox-frame-probe.json
```

It independently reconstructs four-connected objects and bounding-box frames,
then checks every joint exact-axis combination in all three bands, default
canonical-profile coverage, declared witness/rival behavior, 300 held-out lesson
rotations, canonical-shortcut fit, and actual Racket parity. It exits nonzero on
any finding and records the generator SHA and executed rule hash in its JSON.
