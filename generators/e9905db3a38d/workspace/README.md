# Workspace and future-agent checks

The selected implementation is `../generator.py`. The task-local regression
suite is `../tests/test_generator_contract.py`.

From the packet repository root:

```bash
PYTHONPATH=shared/runtime pytest -q \
  generators/e9905db3a38d/tests/test_generator_contract.py
```

The tests cover:

- rule-hash and axis metadata;
- full override-domain acceptance plus unknown-key rejection;
- strict input-shrink relation;
- distinct, rotation-observable templates;
- all four code branches;
- absence of deterministic corner-code leakage;
- canonical-linked support in every band;
- Python-mirror parity on all canonical examples; and
- executable rival/lesson-identifiability contracts.

For repository-level evidence, run the packet command:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check \
  e9905db3a38d --battery --phase after --out ../checks/after
```

Do not place alternate selected implementations here: workspace drafts are not
automatically selected.
