# Workspace

The selected implementation is `../generator.py`.  Workspace files are review
and analysis tools and are not automatically selected as production generators.

## `lesson_probe.py`

A source-bound lesson-level curriculum probe.  It imports the selected generator
by path, records its SHA-256, reads the generator's actual
`LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, schedule, axes, and mirror, and
materializes non-overlapping five-demo plus one-query lessons.

Run from `repo`:

```sh
PYTHONPATH=shared/runtime:src python3 \
  generators/5782a1f38509/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/final-lesson-probe.json
```

Sampling policy:

- bands: easy, medium, hard;
- 100 lessons per band by default;
- seed: first 64 bits of
  `sha256(task|lesson-probe-v1|band|lesson_index)`;
- start index: `lesson_index * 11`;
- demonstrations: `start..start+4`;
- query: `start+5`;
- all five cyclic schedule starts are checked separately.

The probe fails when a declared rival fits every demonstration but changes the
query, when `lesson_identifiable` reports ambiguity, or when a declared canonical
shortcut does not actually fit every canonical pair.  It reports unique inputs,
unique outputs, profile counts, strict-profile support, rival disagreements, and
explicit limitations.  It does not claim to eliminate undeclared hypotheses;
Racket parity is independently covered by rule-smoke and authority checks.
