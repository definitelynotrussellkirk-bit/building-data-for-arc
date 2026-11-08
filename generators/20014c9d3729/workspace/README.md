# Workspace: source-bound probes

`lesson_probe.py` checks a stronger property than per-input witness frequency:
every actual two-demonstration/one-query lesson window must identify the intended
rule against all canonical-compatible rivals declared by the selected generator.
It discovers `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` dynamically, verifies
each rival against all four canonical pairs, and then checks every consecutive
start in a deterministic 100-window schedule for each named difficulty band.

Run from the packet root after the final-source Racket rule-smoke check:

```bash
python3 run_with_racket.py python3 \
  generators/20014c9d3729/workspace/lesson_probe.py \
  --seed 20014 --starts 100 \
  --out ../checks/lesson-probe/report.json
```

The probe uses `rule_mirror` for cheap bulk labels and records the exact generator
SHA-256. Its conclusions are bounded to declared rivals and the sampled episode
assembly; they do not establish universal task identifiability.
