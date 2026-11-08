# Workspace

The selected implementation is `../generator.py`. Workspace experiments are not
automatically selected.

## Cyclic lesson probe

`lesson_probe.py` is a source-bound authoring check for this task. It:

- validates every canonical pair against `self_check` and the Python rule mirror;
- exercises exact boundary overrides for all five scene profiles;
- checks every cyclic start of the five-example schedule in every difficulty band;
- reads `LESSON_COMPETITORS` from the selected generator and verifies every rival
  is refuted by every complete demonstration window; and
- reports unique inputs separately from overlapping lesson-window instances.

Run from the packet root:

```sh
python3 run_with_racket.py python3 generators/e0650802a8fb/workspace/lesson_probe.py \
  --seeds 20 --out ../checks/e0650802a8fb-lesson-probe.json
```

This is an authoring aid, not an intake gate. Its report is bound to the selected
generator SHA-256 and should be rerun after any schedule, profile, or rival change.
