# Workspace

The selected implementation is `../generator.py`; task-local regression tests
are in `../tests/test_generator_8ce1331089a3.py`.

Fast source-only checks from the repository root:

```bash
python3 -m pytest -q generators/8ce1331089a3/tests/test_generator_8ce1331089a3.py
python3 generators/8ce1331089a3/workspace/profile_probe.py --samples 40 --pretty
```

`profile_probe.py` is intentionally cheaper than the portable Racket battery.
It reports canonical-profile coverage, distractor counts, route totals,
semantic witness hits, and named-rival disagreements for every difficulty
band. It does **not** certify Racket parity; use the packet battery for that.
