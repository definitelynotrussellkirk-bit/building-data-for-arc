# Workspace

The selected implementation is `../generator.py`. Workspace probes are
supplementary evidence and are never selected automatically.

## `reflection_audit.py`

Independent replay probe for the repaired reflection curriculum. It:

- loads the selected generator (or `GENERATOR_UNDER_TEST` / `--generator`),
- reads canonical pairs through `reviewer_support`,
- checks canonical validator acceptance and an independent Python oracle,
- draws deterministic samples in each requested difficulty band,
- measures uniqueness, shape/profile support, nondeterminism, identity outputs,
  semantic witnesses, and every live declared rival, and
- checks 12 consecutive production-style three-demo lesson windows per band.

Run from the repository through the packet wrapper:

```bash
python3 run_with_racket.py python3 \
  generators/4a9e2bc51201/workspace/reflection_audit.py \
  --count 100 --bands easy medium hard \
  --out ../checks/reflection-audit.json
```

The final retained report uses seeds `50000 + index`, sample indices
`7*index + 3`, and 100 draws per band. A pass is finite evidence against the
selected generator's declared rivals, not a proof of universal identifiability;
the selected Racket rule remains authoritative.
