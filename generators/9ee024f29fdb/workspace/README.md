# Workspace probes for 9ee024f29fdb

The selected implementation is `../generator.py`. This directory contains
independent, source-bound review helpers; it is not automatically selected at
runtime.

## Reference and distribution helpers

`reference_probe.py` re-expresses the visible cell semantics without importing
production generator helpers. It provides:

- canonical-pair loading and an independent Python authority mirror;
- interior/lattice observations and strict-profile classification;
- exact-axis observation and distribution summaries;
- a cyclic lesson-identifiability CLI that rotates every pair into the query.

From `repo/`, reproduce the final cyclic probe with:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/9ee024f29fdb/workspace/reference_probe.py \
  --starts-per-band 100 --seed-base 808 \
  --output ../checks/cyclic-lesson-probe.json
```

The final command covers 100 starts in each of easy, medium, and hard. With
three demos it evaluates four query rotations per start: 1,200 rotations total.
The report records generator version/hash, exact seed/sample policy, per-band
counts, first failures, and limitations.

This Python probe supplements but does not replace the canonical Racket battery,
authority-sync check, or source-bound lesson census.
