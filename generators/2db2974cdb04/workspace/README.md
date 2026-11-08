# Workspace tools for 2db2974cdb04

Run the independent semantic/distribution audit from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/2db2974cdb04/workspace/hole_extraction_audit.py \
  --per-band 100 --json-out /tmp/2db2974cdb04-audit.json
```

The tool checks all selected canonical pairs with an independent Python region oracle, samples each difficulty band, records exact canonical-profile support and observable axes, and measures disagreement with the generator's declared rivals. It is diagnostic only; Racket remains the label authority.

The smallest retained bbox-shortcut witness is under `../counterexamples/bbox-interior-shortcut/`. Regenerate its Python artifacts with `build.py`, then refresh `racket.json` with the supported `arcpuzzles apply` command recorded in `metadata.json`.
