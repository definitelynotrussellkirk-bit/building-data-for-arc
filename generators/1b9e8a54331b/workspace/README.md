# Authoring workspace for 1b9e8a54331b

The selected implementation is `../generator.py`. Files here are reusable,
source-bound diagnostics and are never selected automatically.

## Semantic contract probe

Run from `WORK/repo` with the packet runtime available:

```sh
python3 generators/1b9e8a54331b/workspace/semantic_contract_probe.py \
  --report ../checks/1b9-semantic-probe/report.json \
  --inputs ../checks/1b9-semantic-probe/inputs.json \
  --expected ../checks/1b9-semantic-probe/expected.json
```

The probe checks ordinary semantic coverage, all exact count/axis boundaries at
14×14, both retained ambiguous lesson windows, and per-band uniqueness. It emits
five representative input grids and Python-mirror expectations for independent
protected-Racket replay. The Python mirror is diagnostic only; Racket remains the
label authority.
