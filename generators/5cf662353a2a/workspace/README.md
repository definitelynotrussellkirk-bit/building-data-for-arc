# Workspace

The selected implementation is `../generator.py`; workspace files are authoring aids and are never selected automatically.

- `probe_size_order.py` dynamically loads the current generator, verifies every declared rival against all canonical labels, generates the deterministic cell-count-vs-bounding-box witness, and writes a source-hashed report.
- `generator_before_2.2.0.py` is the untouched assigned baseline retained for local diagnosis; it is not selected or imported by tests.

The probe reads canonical answers and therefore must not be used during a visible-only solve episode.
