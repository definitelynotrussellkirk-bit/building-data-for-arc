# Review workspace for 981730af48bb

The reusable probes for this repair live in the task-local test module:

```bash
cd repo
pytest -q generators/981730af48bb/tests/test_generator_981730af48bb.py
```

From the packet root, rerun the source-bound admission and lesson checks with:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 981730af48bb \
  --battery --timeout 4000 --phase after --out ../checks/after
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 981730af48bb \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census.json
```

Important regression: do not replace the canonical per-row 2/4 span mixture with
one span per grid. The ordinary envelope gate can miss that restriction; the
`reuse_first_row_half_span` competitor and the leave-one-out tests are the
specific guard.
