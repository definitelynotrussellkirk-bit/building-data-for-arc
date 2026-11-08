# Workspace

The selected implementation is `../generator.py`.

- `generator.before.py` is the byte-for-byte pinned generator inspected before
  the repair; it is retained for a direct source comparison.
- `reference_probe.py` is an independent Python oracle/rival/distribution probe.
  It checks canonical pairs, 128 draws per difficulty band by default, all
  cyclic local lesson/query rotations, an exact color-blind counterexample, and
  optional real-Racket parity. It deliberately does not reuse the generator's
  semantic mirror.

Workspace drafts are never automatically selected. The production regression
suite is in `../tests/test_generator.py`.
