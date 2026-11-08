# Workspace

The selected implementation is `../generator.py`; workspace files are reviewer tools, not alternate selected generators.

## `lesson_distribution_probe.py`

This source-bound probe measures the production generator's default four-pair lessons without Racket:

```bash
python3 repo/generators/e99db71ae23d/workspace/lesson_distribution_probe.py \
  --seeds 100 \
  --out checks/lesson-distribution-final.json \
  --require-rotations
```

For each requested band it records:

- exact-input unique count and fraction;
- maximum replay multiplicity and total excess replays;
- scene-profile counts;
- lesson windows containing duplicate inputs;
- `lesson_identifiable` results for every cyclic query position.

The report includes the selected generator SHA-256, seed range, sample indices, and denominator. It is deliberately complementary to the Racket-backed `lesson-census`: this probe cheaply exposes deterministic schedule concentration and exhausts all four query positions for the same simple seed range, while the census supplies authoritative labels, SHA-derived seeds, and retained rival predictions.
