# Proposed `output_extent` parameter

This task-local prototype keeps the canonical periodic-tile recovery algorithm
and changes only its output extent:

- `full_grid` (canonical/default): repeat the recovered tile over the original grid;
- `tile_only` (proposed): return one recovered clean period tile.

The parameter is fixed for the whole episode. All labels are executed by the
exact materialized Racket program. The writer rejects an existing visible-content
ID instead of silently overwriting a duplicate challenge. The public challenge contains only visible
training pairs and query inputs; its filename is the SHA-256 of those exact
visible bytes. This prototype does not change production generation, catalog
approval, or training admission.

From the packet root, materialize a three-demo/four-query episode for each value:

```bash
python3 review.py run python3 generators/8dd7ace7de9a/workspace/parametric/prototype.py \
  --seed 73001 --parameter tile_only --n-train 3 --n-test 4 \
  --out-dir ../checks/parametric/output-extent/tile-only
python3 review.py run python3 generators/8dd7ace7de9a/workspace/parametric/prototype.py \
  --seed 73002 --parameter full_grid --n-train 3 --n-test 4 \
  --out-dir ../checks/parametric/output-extent/full-grid
```
