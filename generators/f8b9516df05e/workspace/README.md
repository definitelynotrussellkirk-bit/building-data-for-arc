# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

- `baseline_generator.py` — immutable review copy of the assigned v3.1.0 source, retained to reproduce the original validation/control defects.
- `reference_probe.py` — independent Python rule mirror, observable-axis extractor, malformed-grid fixtures, and two plausible rivals (`skip_unit_gap`, `ignore_blocker`). Focused tests compare the selected generator's declarations against these independent implementations.

Authoritative labels remain Racket-produced. The Python mirror is only a parity/debugging probe.

Primary replay commands are recorded in the packet-level `RESULTS.json`; decisive outputs are under `checks/before`, `checks/after`, `checks/task-tests`, and `checks/lesson-census.json`.
