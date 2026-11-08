# Review workspace for `7b0cb3b9a618`

The selected implementation is `../generator.py`. Files here are retained
review tools, not alternate selected generators.

## `reference_probe.py`

An independent, source-bound probe for future reviewers. It does **not** use the
production rule helper for labels. It:

- reproduces the clean-row / one-anomaly rule in Python;
- validates the six canonical joint profiles from pixels;
- loads an arbitrary candidate through `GENERATOR_UNDER_TEST` or `--generator`;
- reads `LESSON_COMPETITORS` dynamically rather than copying rival names;
- exhausts all 12 deterministic schedule starts and all 4 query rotations per
  four-pair lesson; and
- samples each difficulty band, retaining profile, answer, uniqueness, source
  hash, structural-failure, and ambiguity counts.

From the packet root:

```sh
PYTHONPATH=repo:repo/shared/runtime \
python3 repo/generators/7b0cb3b9a618/workspace/reference_probe.py \
  --samples 120 --seed 190807 --out checks/reference-probe.json
```

The final retained report has zero structural failures and zero declared-rival
ambiguities. The probe is finite: it checks the declared schedule and rivals,
not every conceivable alternative rule.

## `parametric/`

Proposed front/back endpoint selection with exact canonical default, protected
Racket labels, configurable demonstrations and queries, and a public-byte-safe
batch writer. See `parametric/README.md` for the four-query command, limits and
focused tests. This workspace does not change canonical approval or training
admission.
