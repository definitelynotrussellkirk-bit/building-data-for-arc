# Workspace

The selected implementation is `../generator.py`; workspace files are authoring
and review aids and are never selected as the generator.

## Semantic probe

`semantic_probe.py` is a source-bound, reproducible check for the failure that
motivated this repair: a complete lesson can still permit a plausible shortcut
even when individual examples look diverse. It reads the generator's actual
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS` declarations,
verifies that each declared canonical shortcut really fits all canonical pairs,
and checks complete four-example lessons at every requested cyclic start.

From the packet root:

```sh
python3 run_with_racket.py python3 \
  generators/dc0a7662670b/workspace/semantic_probe.py \
  --per-band 100 --cyclic-starts 8 \
  --out ../checks/semantic-probe.json
```

The production `lesson-census` remains the authoritative materialized-lesson
sample. This smaller task-local probe adds the missing cyclic-start coverage and
keeps the declared-rival list source-bound. Its finite domain is explicit: a
clean report does not prove universal induction or exclude undeclared rivals.
