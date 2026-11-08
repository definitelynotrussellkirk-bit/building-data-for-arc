# Workspace

The selected implementation is `../generator.py`. Workspace files are
reviewer-side probes and are not selected as the generator.

- `reference_probe.py` is an independent implementation of left-priority mirror
  completion, the two canonical-fitting rivals, orbit counts, canonical profile
  extraction, and a minimal lawful conflict witness.
- `verify_lesson_census.py` validates a completed 300-lesson shared census when
  the shared canonical reader encounters a normal unlabeled ARC query. It is
  deliberately fail-closed: it accepts only that exact reader error, verifies
  every saved lesson and rotation, binds the report to the current generator
  hash, checks all labeled canonical pairs, and retains the original shared
  report as `error`.

Portable tests for both tools live in `../tests/`.
