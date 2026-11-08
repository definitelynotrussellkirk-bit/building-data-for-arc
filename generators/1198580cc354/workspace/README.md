# Review workspace guide

The selected implementation is `../generator.py`; task-local regression tests
are in `../tests/test_generator.py`.

Reusable inspection API for future agents:

- `rule_mirror(grid)` — independent Python implementation of the selected rule;
- `observe_overrides(grid)` — recovers all three exact public axes;
- `strict_canonical_like(grid)` — structural grammar check;
- `schedule_profile(seed, sample_index, difficulty)` and
  `SCHEDULE_PROFILES` — auditable curriculum schedule;
- `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`,
  `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` — executable alternatives;
- `lesson_identifiable(demos, query)` — checks labeled lessons against those
  alternatives;
- `mutation_fixtures()` — malformed task-linked near misses for validator
  sensitivity checks.

Run the focused tests from the repository root with:

```bash
PYTHONPATH=shared/runtime python3 -m pytest -q \
  generators/1198580cc354/tests/test_generator.py
```

Do not treat the finite named-rival pass as universal identifiability. Add a new
executable rival and witness when a concrete shortcut is discovered.
