# Review workspace: cf4fdf474ad5

The selected implementation is `../generator.py`. Reusable probes are deliberately kept beside it rather than in an unselected draft:

- `../tests/test_review_repair.py` — 51 portable regressions covering canonical parity, exact controls, malformed inputs, six semantic rivals, every cyclic three-demo window, query rotations, and the retained counterexample.
- `../counterexamples/top-left-on-tie/` — exact normal-draw witness for the canonical-fitting tie shortcut.
- `../../../checks/shortcut/` — supported `arcpuzzles apply` receipt and source-bound metadata.

Useful commands from `WORK/`:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check cf4fdf474ad5 \
  --battery --timeout 4000 --phase after --out ../checks/after

python3 run_with_racket.py python3 -m arcpuzzles check cf4fdf474ad5 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests

python3 run_with_racket.py python3 -m arcpuzzles lesson-census cf4fdf474ad5 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json

python3 run_with_racket.py python3 -m arcpuzzles apply cf4fdf474ad5 \
  --input ../checks/shortcut/input.json --out ../checks/shortcut/racket-replay.json
```

The Python mirror and rivals are review diagnostics, never label authority. Use the supported Racket runner for authoritative outputs.
