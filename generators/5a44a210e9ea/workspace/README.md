# Review workspace

The selected implementation is `../generator.py`; workspace files are independent probes, not alternate selected generators.

- `reference_probe.py` provides a small independent component/frame oracle, canonical-pair loader, declared-rival mirrors, override observation, and optional real-Racket parity execution. Its geometry code deliberately does not call production geometry helpers.
- `lesson_rotation_probe.py` consumes a shared lesson-census JSON file and re-scores every materialized lesson with each pair rotated into the query slot. It catches slot-order fragility that the production fixed-query census cannot see.

Example from the packet repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/5a44a210e9ea/workspace/lesson_rotation_probe.py \
  ../checks/lesson-census-final-v3.json \
  --out ../checks/lesson-rotation-final-v3.json
```
