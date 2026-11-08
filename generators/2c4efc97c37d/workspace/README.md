# Workspace for 2c4efc97c37d

The selected implementation is `../generator.py`. Workspace tools are reviewer-owned diagnostics and are never automatically selected.

## `onion_probe.py`

This probe intentionally does not import production geometry helpers. It independently:

- finds binary foreground components while treating 0 and 9 as background;
- computes cardinal onion depth;
- evaluates bounding-box thickness, one-object-per-color, and nonzero-foreground rivals;
- observes all exact generator axes; and
- supplies both the original bounding-box witness and the combined binary-mask witness.

From the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 generators/2c4efc97c37d/workspace/onion_probe.py
```

The combined witness has intended output `[[1,2,3]]`; the three rival outputs are `[[2,2,3]]`, `[[2,2,1]]`, and `[[1,2,3,1]]`.

## `binary_mask_census.py`

This independent source-bound checker exercises exact override boundaries, both scheduled palette topologies, isolated color-9 placement, production/independent output agreement, and all three rivals.

Quick two-case smoke:

```bash
PYTHONPATH=src:shared/runtime python3 generators/2c4efc97c37d/workspace/binary_mask_census.py
```

Full 512-case boundary census:

```bash
PYTHONPATH=src:shared/runtime python3 generators/2c4efc97c37d/workspace/binary_mask_census.py \
  --full --out /tmp/2c4efc97c37d-binary-mask-census.json
```

The retained full report is `WORK/checks/binary-mask-census/report.json`.
