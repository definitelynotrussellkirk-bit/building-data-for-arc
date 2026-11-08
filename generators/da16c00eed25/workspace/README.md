# da16c00eed25 review workspace

`lesson_probe.py` is a source-bound lesson-level audit. It stages the same
portable runtime used by `arcpuzzles check`, labels generated grids through the
selected Racket authority, and reads the generator's live
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and witness declarations.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/da16c00eed25/workspace/lesson_probe.py \
  --lessons-per-band 100 --out ../checks/lesson_probe.json
```

The report verifies canonical shortcut fit, inspects 100 four-demo/one-query
lessons in each difficulty band, records unique-input counts and domain limits,
and tests every cyclic schedule start. A pass is finite evidence only; it does
not establish unique or universal induction.
