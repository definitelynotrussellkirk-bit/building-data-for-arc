# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected.

## Reusable counterfactual witness probe

`witness_specificity_probe.py` checks that a declared semantic witness is the
actual reason its paired rival fails. It requires a matched negative control
where the witness is absent and the rival agrees with the authority, plus a
positive example where the witness is present and the rival disagrees.

From the repository root:

```bash
python3 generators/5d6fcce80b6a/workspace/witness_specificity_probe.py \
  --out ../checks/witness_specificity_probe.json
python3 -m pytest -q \
  generators/5d6fcce80b6a/workspace/test_witness_specificity_probe.py
```

The probe is deliberately Racket-free: it tests the integrity of the Python
semantic contract after ordinary rule-mirror parity has been established by the
battery. Its fixed controls are also regression examples for the data-quality
gate proposed in `QUESTION_ANSWER.md`.
