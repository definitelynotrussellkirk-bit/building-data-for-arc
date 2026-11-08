# Workspace

The selected implementation is `../generator.py`; workspace files are support
artifacts and are not selected automatically.

## Motion-semantics probe

`motion_semantics_probe.py` checks the authority detail most easily lost in a
plain-language summary: each component moves against walls plus its unchanged
source footprint. It verifies that a labeled canonical input exposes this
behavior and that generated scenes pair a source-blocked object with an
ordinary wall-docking object. It also requires source-stop distances 1 and 2
and support for every movable color 1–8.

From the packet root:

```bash
python3 repo/generators/f0d16ecf2012/workspace/motion_semantics_probe.py \
  --draws 240 --difficulty hard \
  --out checks/motion_semantics.json
```

The command exits nonzero if any required regime, distance, rival disagreement,
canonical witness, or color is absent. The JSON records the generator SHA-256.

## Correlation probe

`correlation_probe.py` measures dataset-level shortcuts that ordinary per-grid
semantic witnesses cannot detect: fixed split-witness lane, fixed split slope,
small connected-witness vocabulary, always-distinct lane palettes, and a fixed
canonical-anchor slot.

```bash
python3 repo/generators/f0d16ecf2012/workspace/correlation_probe.py \
  --draws 240 --difficulty hard \
  --out checks/correlation_probe.json
```

The command exits nonzero when either two-lane role, either diagonal slope,
fewer than four connected profiles, either palette mode, all three anchor
slots, or exactly one anchor per three-sample block is absent. Its JSON is also
source-bound.
