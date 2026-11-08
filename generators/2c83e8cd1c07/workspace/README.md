# Review workspace: 2c83e8cd1c07

The reusable probes for this repair live in `../tests/test_generator.py` and intentionally read the generator's actual rival declarations rather than maintaining a second rival-name list.

Useful commands from the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 2c83e8cd1c07 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests

python3 run_with_racket.py python3 -m arcpuzzles lesson-census 2c83e8cd1c07 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json
```

The focused tests cover exact override extrema in every band, malformed inputs, destructive mutations, deterministic default schedules, canonical compatibility, the blocked-diagonal witness, and all short cyclic three-demonstration windows. `generator.rule_mirror` is only a diagnostic oracle; use the supported Racket runner for label-authority evidence.
