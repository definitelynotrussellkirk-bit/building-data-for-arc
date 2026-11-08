# 4c26a1072222 review workspace

## `lesson_probe.py`

A source-bound whole-lesson census for the repaired generator. It imports the
final generator bytes, iterates the actual `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`, verifies each declared shortcut
against every unique usable canonical pair, and mirrors the production runner's
four-demo/one-query sequential sampling and duplicate rejection.

From `repo/`:

```bash
python3 generators/4c26a1072222/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/lesson-probe.json
```

The report records source hashes, seed ranges, actual sample indices,
unique-input/pair counts, disagreements, survivor counts, witnesses, observed
D4 branches, domain limits, and both the production start and every cyclic
schedule start. Its output oracle is the task-local Python mirror for speed;
independent live-Racket parity remains the responsibility of the retained
repository battery reports.
