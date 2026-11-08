# Workspace

The selected implementation is `../generator.py`; this directory holds reusable
review tooling rather than alternate selected source.

## Shortcut and lesson probe

`shortcut_probe.py` reads the generator's declared witnesses, rivals, and lesson
competitors. It independently computes the exact-corner output, reports which
rivals fit canonical train demonstrations but fail the canonical test, samples
all four difficulty modes, and checks every requested cyclic lesson start.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/59ccf6f5cc65/workspace/shortcut_probe.py \
  --per-band 32 --lesson-starts 32 \
  --out ../checks/shortcut-probe-final.json
```

Exit status is nonzero for oracle mismatches, false witness claims, a surviving
query-changing competitor, or a disagreement between `lesson_identifiable` and
the executable competitors. The report includes the exact generator SHA-256 and
any concrete canonical counterexample grids.
