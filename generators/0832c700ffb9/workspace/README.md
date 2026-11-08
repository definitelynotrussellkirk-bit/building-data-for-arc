# Review workspace: 0832c700ffb9

`probe_curriculum.py` is a replayable finite audit of the repaired generator. It
loads the generator's actual `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`,
`WITNESS_RIVALS`, and `LESSON_COMPETITORS`; checks the Python mirror against all
canonical labels; exhausts every legal joint public override in all four bands;
and tests every single-query rotation of overlapping six-pair schedule windows.

From the packet root:

```bash
PYTHONPATH=repo/shared/runtime python3 \
  repo/generators/0832c700ffb9/workspace/probe_curriculum.py \
  --per-band 12 --out checks/curriculum-probe-final.json
```

The tool's labels come from `rule_mirror`, so it is a cheap authoring/regression
probe, not a replacement for the source-bound Racket battery or lesson census.
Its JSON records the generator hash, finite sample sizes, unique-input count,
canonical shortcut fit, override failures, witness hits, and exact ambiguous
rotations if any.
