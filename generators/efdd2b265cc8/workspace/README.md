# Review workspace

`review_probe.py` is a replayable, source-bound diagnostic for this generator.
It checks canonical acceptance, every exact integer-axis combination,
deterministic/fresh generation, global RNG purity, declared D4 competitors, and
all query rotations in finite four-example lessons.

From the repository root:

```bash
PYTHONPATH=shared/runtime python generators/efdd2b265cc8/workspace/review_probe.py \
  --seeds-per-case 1 --lesson-starts 16 \
  --out ../checks/efdd2b265cc8-review-probe.json
```

This Python probe is diagnostic only. The packet's Racket-backed checks remain
label authority.
