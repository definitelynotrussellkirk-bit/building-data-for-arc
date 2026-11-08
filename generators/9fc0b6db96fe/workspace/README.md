# Workspace for 9fc0b6db96fe

The selected implementation is `../generator.py`; workspace code is review tooling only.

- `reference_probe.py` is an independent Python oracle and structural probe. It reads canonical examples, reconstructs legend/body order, mirrors crop/transform/pack behavior, recovers advertised axes, and can compare a batch against the selected Racket authority when Racket is available. It never silently substitutes Python output for Racket output.
- `lesson_census.py` must run inside a prepared source-bound ARC runtime. It uses `scripts.generator_semantic_gate.materialize_lessons`, canonical Racket labels, 100 lessons per band by default, and all four cyclic choices of query position. It invokes the generator's actual `LESSON_COMPETITORS` and `lesson_identifiable` declarations and reports unique-input counts and surviving rivals.

Example from a prepared runtime:

```sh
PYTHONPATH="$RUNTIME" RACKET_PATH="$RACKET" \
  python3 /path/to/workspace/lesson_census.py --lessons 300 --out lesson-census.json
```

The focused regression suite is in `../tests/test_generator_9fc0b6db96fe.py`.
