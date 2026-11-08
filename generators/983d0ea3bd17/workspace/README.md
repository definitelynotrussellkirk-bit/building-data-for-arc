# Workspace

The selected implementation is `../generator.py`. Workspace files are task-local review tools or experiments and are never automatically selected as the generator.

## `deep_audit.py`

Run the adversarial curriculum audit from the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/983d0ea3bd17/workspace/deep_audit.py \
  --bands easy medium hard \
  --seeds 1 91 20260929 \
  --starts 0:24 \
  --out ../checks/deep-audit.json
```

It checks four things:

1. every declared `CANONICAL_SHORTCUTS` rule fits every canonical pair;
2. no named `LESSON_COMPETITORS` rule survives any sliding three-demo window;
3. each scheduled blocker probe has two distinct colors, an edge source, an aligned pair, and two independently observable stops;
4. `lesson_identifiable` agrees with the materialized demonstrations and next query.

To test a newly suspected shortcut, add it to the generator’s rival declarations and rerun this tool. Any survivor is reported with band, seed, start index, schedule profiles, and rival name.
