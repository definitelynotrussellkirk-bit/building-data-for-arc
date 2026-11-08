# Review workspace for `1e07c169ac61`

`reference_probe.py` is an implementation-independent geometry oracle and exact
axis observer used by the portable task tests. It computes the selected
anchor-centered clockwise rotation without importing production helpers.

`schedule_probe.py` exhausts starts of the four-slot curriculum, materializes
five-pair windows, holds out every pair once, and scores the selected generator's
three declared competitors. Run from this directory or from the repository with
`PYTHONPATH=shared/runtime` available, for example:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/1e07c169ac61/workspace/schedule_probe.py \
  --cycles 8 --out ../checks/schedule-probe.json
```

The probe is fast Python evidence, not label authority. The official
`arcpuzzles lesson-census` result in the review return is Racket-backed. Both are
finite declared-rival checks, not a proof that every possible induced rule is
identified.
