# Task-local review workspace

`review_probe.py` is a reusable, source-hashed contract probe for the selected
`../generator.py`. It exhausts all 1,080 advertised joint override combinations,
verifies every declared `CANONICAL_SHORTCUTS` entry against canonical labels,
and counts default semantic witnesses/rival refutations per difficulty band.

From the packet root:

```sh
PYTHONPATH=repo/shared/runtime:repo/src \
  python3 repo/generators/8f6a6ec3ae21/workspace/review_probe.py \
  --default-per-band 100 --out checks/semantic-probe.json
```

The probe is intentionally local and fast. Racket parity remains the job of the
battery's `rule_smoke` stage; finite named-rival coverage is not a proof of unique
induction against every possible rule.
