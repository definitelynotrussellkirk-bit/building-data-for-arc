# Workspace and reusable probes

The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

The maintained contract probe is `../tests/test_generator_contract.py`. It is intentionally portable through `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`, and checks:

- all five canonical input/output pairs against `self_check` and the Python mirror;
- exact `grid_h`/`grid_w` controls, invalid values, and deterministic replay;
- canonical-profile support and marker-count bounds;
- the extended-color and stable-order witnesses;
- 24 consecutive lesson starts in each difficulty band, with every one of the four labelled pairs rotated into query position.

Run it through the source-bound wrapper from the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check b5af3d6b3cd5 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

For a larger production-sampler probe, use the retained 100-lessons-per-band census command recorded in `RESULTS.json`. Its declared-rival result is evidence for this finite schedule only.
