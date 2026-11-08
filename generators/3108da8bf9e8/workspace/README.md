# Workspace

The selected implementation is `../generator.py`. This directory contains review probes and retained reports; it is not imported by normal generation.

## `semantic_support_probe.py`

Compares the rule-relevant omitted-count signature across canonical inputs, the frozen baseline, and deterministic repaired samples.

```bash
PYTHONPATH=shared/runtime python3 generators/3108da8bf9e8/workspace/semantic_support_probe.py
```

## `shortcut_census.py`

Measures rank-position map support, displacement, declared-rival matches, exact texture-mask support, all 280 three-groups-of-three local sorting hypotheses, and fixed/local survivor sets across lessons.

```bash
PYTHONPATH=shared/runtime python3 \
  generators/3108da8bf9e8/workspace/shortcut_census.py \
  --per-band 400 --lessons-per-band 96 --seed 20261002
```

The command writes `shortcut_census_report.json` and exits nonzero when a threshold fails. Schema v2 also reports moved-row/column support and local-partition survivor histograms.

## `verify_cycle_partition_equivalence.py`

Checks the generator's fast cycle-packing predicate against an independent brute-force assignment for all 30 integer partitions of nine.

```bash
PYTHONPATH=shared/runtime python3 \
  generators/3108da8bf9e8/workspace/verify_cycle_partition_equivalence.py
```

## `audit_probe.py`

Reproduces the two independently assigned findings-only audit measurements retained in `AUDIT.md`.
