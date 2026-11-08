# Workspace

The selected implementation is `../generator.py`; workspace files are probes,
not automatically selected production code.

## Coverage probe

Run from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/ba9d8eb0cd5a/workspace/coverage_probe.py \
  --per-band 100 --out ../checks/coverage-probe.json
```

The probe loads the selected source bytes, checks every draw with the task
validator and an independent stable-compaction oracle, verifies the exact-axis
observer, and reports canonical-profile support plus disagreement with the
sort-then-pack rival. Failures retain replay seed/sample coordinates.
