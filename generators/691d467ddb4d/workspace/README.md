# Review workspace for 691d467ddb4d

The selected implementation is `../generator.py`. Files here are reusable
review tooling and are not label authority.

## `reference_probe.py`

This helper deliberately reimplements 4-connected component extraction, target
ranking, the intended output, and two shortcut outputs instead of importing the
generator's private helpers. It also provides a source-bound distribution
census. Canonical examples are read through portable `reviewer_support`
`find_root`, `canonical_path`, and `canonical_pairs` helpers, so the same tests
work in the copied task-test runtime and in a fresh packet extraction.

Run from the repository root:

```bash
python3 generators/691d467ddb4d/workspace/reference_probe.py \
  --draws-per-band 200 \
  --out ../checks/after-probes/691d467ddb4d_reference_census.json
```

The retained final report is under
`checks/after-probes/691d467ddb4d_reference_census.json` in the review return.
It is an independent Python observation; canonical labels remain the Racket
program's responsibility.
