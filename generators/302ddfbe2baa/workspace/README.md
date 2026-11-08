# Workspace: 302ddfbe2baa

The selected implementation is `../generator.py`. Workspace files are support artifacts and are never selected automatically.

## `reference_probe.py`

A portable, independent semantic probe for future reviewers. It:

- loads canonical pairs through the public canonical-data helper;
- verifies every declared canonical shortcut fits every usable canonical pair;
- uses an independent Python rule oracle;
- iterates the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` registries;
- checks all cyclic three-example windows for two seeds and every difficulty band;
- reports profile counts, unique inputs, source hashes, and any surviving competitors.

Run from repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/302ddfbe2baa/workspace/reference_probe.py \
  --starts 100 \
  --out ../checks/reference-probe-verification.json
```

A nonzero exit means the generator/rule binding, canonical shortcut premise, or cyclic lesson contract failed.
