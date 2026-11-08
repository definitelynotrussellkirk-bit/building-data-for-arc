# Workspace

- `generator_v2_original.py` is the unmodified imported generator retained for a direct before/after diff.
- `semantic_probe.py` is a source-bound reusable probe. It imports the selected generator, discovers `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`, verifies shortcut fit on canonical pairs, and evaluates overlapping scheduled lessons with exact source hashes.

Run from `repo/`:

```bash
python3 generators/a2d296c74658/workspace/semantic_probe.py \
  --lessons-per-band 128 \
  --out ../checks/semantic/a2d296c74658_final_semantic_probe.json
```

The selected implementation is `../generator.py`; workspace drafts are never automatically selected.
