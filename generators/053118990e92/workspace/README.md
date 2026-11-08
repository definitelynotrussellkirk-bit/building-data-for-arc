# Workspace

The selected implementation is `../generator.py`. Workspace files are support
tools only and are never selected as generators.

## `cyclic_lesson_probe.py`

This source-bound audit complements the shared lesson census by rotating every
pair in a five-pair schedule window into the query position. It reads the live
`LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, and `SEMANTIC_WITNESSES`
declarations, checks every schedule start, verifies each declared canonical
shortcut against all usable canonical pairs, and records exact generator and
input hashes.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/053118990e92/workspace/cyclic_lesson_probe.py \
  --seeds 100 --bands easy,medium,hard \
  --out ../checks/cyclic-lesson-probe.json
```

A nonzero exit means at least one generated pair was invalid, a declared
canonical shortcut failed to fit a canonical pair, or a cyclic rotation left a
declared rival alive. This remains a finite declared-rival audit, not proof of
universal inductive identifiability.
