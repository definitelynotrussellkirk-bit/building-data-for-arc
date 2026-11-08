# Workspace

The selected implementation is `../generator.py`.

## `lesson_probe.py`

A reusable, source-bound Racket-backed curriculum census. It:

- stages the selected generator/runtime rather than importing mutable repository internals in place;
- materializes lessons with the official `scripts.generator_semantic_gate.materialize_lessons` sampler;
- obtains outputs from the selected canonical Racket rule;
- reads `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, semantic witnesses, and `lesson_identifiable` from the generator instead of copying rival names;
- records generator/probe/runtime hashes, per-band seeds and sample starts, schedule residues, unique-input and unique-lesson counts, domain failures, witness hits, canonical shortcut fit, and competitor survival;
- limits its claim to the finite pinned census.

Run from the packet root with a fresh output path:

```sh
python3 run_with_racket.py python3 generators/2dae2c34641b/workspace/lesson_probe.py \
  --per-band 100 --schedule-modulus 3 \
  --out ../checks/semantic-lessons/lesson-probe-rerun.json
```

The retained final report is `checks/semantic-lessons/lesson-probe.json`.
