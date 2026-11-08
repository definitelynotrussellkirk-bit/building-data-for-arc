# Workspace

The selected implementation is `../generator.py`.

## Reusable distribution probe

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/c7f337af82e5/workspace/probe_distribution.py \
  --seeds 16 --starts 40 --out ../checks/distribution.json
```

The probe reads the current rival registries, verifies claimed canonical fits,
checks every requested consecutive lesson start and query rotation, and records
source hashes, distinct-input counts, and exact counterexamples. It uses an
independent Python interpretation, not the Racket authority or production
rejection sampler. It also runs as an absolute script from another directory
without a predefined Python import path, using only this checkout's helpers.

For authoritative production evidence, use a new output path:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census c7f337af82e5 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json
python3 run_with_racket.py python3 -m arcpuzzles check c7f337af82e5 \
  --stage task_tests --phase after --out ../checks/task-tests
```

The probe never changes generator code or approval status. Preserve production
rejections separately: a clean direct-window result cannot substitute for the
production census.
