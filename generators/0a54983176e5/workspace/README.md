# Workspace

The selected implementation is `../generator.py`. Workspace files are review
probes and are not automatically selected by the runtime.

## Semantic lesson-window probe

`semantic_window_probe.py` reads the generator's actual `EXAMPLES_NEEDED`,
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `rule_mirror`, and
`lesson_identifiable` declarations. It verifies that declared shortcuts fit all
canonical pairs and that every requested consecutive lesson window refutes every
declared competitor.

From the repository root:

```sh
python3 generators/0a54983176e5/workspace/semantic_window_probe.py \
  --seed-start 910000 --seed-count 16 --start-count 9 \
  --difficulties easy,medium,hard \
  --out ../checks/0a54983176e5_semantic_window_probe.json
```

This is a cheap Python preflight. The Racket-backed `lesson-census` remains the
source-bound final check.
