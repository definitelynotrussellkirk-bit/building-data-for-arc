# Reviewer workspace for fa5bb24054bc

The selected implementation is `../generator.py`. These tools are retained for future reviewers and are not label authority.

## `reference_probe.py`

Independent geometry/oracle helpers. It reads canonical pairs through the packaged canonical ledger, splits panels without importing production geometry, independently counts holes, computes relation matrices, observes exact axes, and constructs the minimal area-only witness.

## `qualify.py`

A replayable task-local audit that complements the shared battery and lesson census. It checks:

- every requested cyclic four-example lesson start;
- all 60 legal joint combinations of `grid_h`, `n_panels`, and `sep_width`;
- canonical fitting of the generator's declared shortcuts;
- shortcut refutation on generated samples;
- self-check results, ARC width, input/output diversity, and canonical-profile support.

Final command used from `repo/`:

```sh
PYTHONPATH=shared/runtime python3 generators/fa5bb24054bc/workspace/qualify.py \
  --per-band 100 --window-starts 64 \
  --out ../checks/task-local-qualification-v1.json
```

The final report is source-bound to generator SHA-256 `d659db585ae666b9c525b250c09f624da3070624bf9b9c54872e0af366cfbfe3` and reports `status: pass`.
