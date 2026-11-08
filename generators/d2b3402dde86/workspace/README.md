# Distribution and teaching probe

The selected implementation is `../generator.py`. This directory contains a
reusable authoring probe; it never substitutes for Racket reference labels.

From the review packet's `WORK` directory:

```bash
python3 run_with_racket.py python3 generators/d2b3402dde86/workspace/probe_distribution.py --samples-per-band 128 --window-starts 40 --seed 17 --out ../checks/new-distribution.json
```

Use a new output filename. The tool imports the current selected generator,
finds canonical data through the portable shared helpers, and dynamically
reads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`. It reports canonical fit,
geometry, palettes, strict support, blank answer borders, unique input counts,
every requested consecutive start, and all four query holdouts. It retains
small observed counterexamples, failures, and source hashes.

`label_basis` is `python_rule_mirror_diagnostic_only`. For authoritative lesson
evidence, use the shared `arcpuzzles lesson-census` command with
`--per-band 100 --rotate-query`. For an exact witness, use `arcpuzzles apply`
with its input grid. Neither finite probe proves universal identifiability.

Counts are bounded and must be positive; existing output files are preserved.
Generator, validation, rival and ambiguity failures produce a retained JSON
report and nonzero exit. CLI regressions live in `../tests/` and run both in
the source checkout and the materialized task-test runtime.
