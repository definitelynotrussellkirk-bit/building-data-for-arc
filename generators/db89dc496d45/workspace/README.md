# db89dc496d45 workspace

The selected implementation is `../generator.py`; workspace files are authoring and replay tools, not automatically selected.

## Shortcut probe

Run from the extracted packet root:

```sh
PYTHONPATH=repo/src:repo/shared/runtime \
python3 repo/generators/db89dc496d45/workspace/shortcut_probe.py \
  --starts 12 --seed-base 730000 --out checks/shortcut-probe.json
```

The probe imports the selected source, discovers `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`, and then checks:

- each declared shortcut fits every canonical pair;
- each competitor disagrees on generated inputs;
- every four-demo held-out-query rotation distinguishes every competitor;
- each public canvas profile supports both semantic witness types;
- source/rule hashes, replay seeds, dimensions, and per-band schedules are retained.

A green result is finite evidence against the declared rivals, not universal identifiability. Extend the rival set when a new canonical-fitting hypothesis is found; do not hard-code a pass around current names.
