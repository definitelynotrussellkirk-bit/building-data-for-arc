# Workspace

The selected implementation is `../generator.py`. Workspace files are review/authoring tools and are never selected as label authority.

## `reference_probe.py`

Independent Python geometry oracle for task `cf787ae40567`. It recomputes seed locations, clipped plus masks, set unions, edge/overlap signatures, and the two canonical-fitting rivals without importing production geometry helpers. Task tests use it to catch mirror drift.

## `lesson_probe.py`

Compact cyclic lesson audit built on the independent oracle. It reads the generator's live `LESSON_COMPETITORS`, so future rival additions are automatically covered.

From the packet root:

```sh
python3 run_with_racket.py python3 \
  generators/cf787ae40567/workspace/lesson_probe.py \
  --seeds 64 --starts 4 \
  --out ../checks/final-reference-probe.json
```

The report checks four-demo/one-query windows for all three difficulty bands, records source hashes and unique inputs, verifies the independent oracle, and fails if a declared rival survives every demonstration. This finite probe does not replace Racket parity or the production `lesson-census` command.
