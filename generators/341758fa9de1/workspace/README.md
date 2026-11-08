# Workspace

The selected implementation is `../generator.py`.

`probe_curriculum.py` is a source-level regression aid for future edits. It:

- loads the task's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`;
- verifies every declared canonical shortcut against every public labeled pair;
- enumerates cyclic lesson starts and every held-out query position; and
- records generator hashes, rival disagreements, ambiguities, and limitations.

From the packet root:

```sh
python3 run_with_racket.py python3 generators/341758fa9de1/workspace/probe_curriculum.py \
  --starts 24 --seeds 12317 12319 12323 12329 \
  --out ../checks/cyclic-lesson-probe.json
```

This probe uses an independent Python rule mirror. It complements, but does not
replace, the Racket-labeled shared semantic gate and lesson census.
