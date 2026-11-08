# Workspace

`probe_shortcuts.py` is a replayable adversarial audit for the selected generator. It reads the generator's actual `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `LESSON_COMPETITORS` declarations; verifies every rival against every canonical pair; emits generated witness grids; and checks every cyclic start of the four-example schedule.

Run from the repository root:

```sh
PYTHONPATH=shared/runtime python3 generators/2692a3e47a66/workspace/probe_shortcuts.py \
  --seed 71 --start-index 0 --difficulty medium --out ../checks/shortcut-probe.json
```

The selected implementation remains `../generator.py`; workspace tools are not automatically selected.
