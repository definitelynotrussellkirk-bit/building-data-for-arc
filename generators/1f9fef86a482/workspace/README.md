# Workspace

The selected implementation is `../generator.py`; workspace tools are diagnostic
and are never automatically selected.

- `reference_probe.py` independently extracts same-colour components, builds the
  contact graph, computes the intended output, and implements review rivals.
  Set `GENERATOR_UNDER_TEST` to compare another retained source.
- `lesson_probe.py` materializes deterministic four-pair blocks, rotates every
  pair into the query position, imports the generator's actual rival registries,
  checks canonical-shortcut fit, and emits a compact JSON report.

These tools are intended for future reviewers and curriculum changes, not as a
replacement for the canonical Racket authority.
