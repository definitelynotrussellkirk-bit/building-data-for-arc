# Workspace

The selected implementation is `../generator.py`; unfinished drafts should stay here and are never selected automatically.

Focused regression command from the packet root:

```bash
pytest -q repo/generators/2496d7db1883/tests/test_generator_2496d7db1883.py
```

Official checks:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 2496d7db1883 --stage lint --phase after --out ../checks/lint
python3 run_with_racket.py python3 -m arcpuzzles check 2496d7db1883 --battery --phase after --out ../checks/after
```

The semantic hooks in `generator.py` are the reusable probe surface for future agents:
`expected_output`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable`.
