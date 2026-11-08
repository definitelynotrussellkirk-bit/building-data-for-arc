# Proposed sort-key parametric family

This task-local prototype keeps the canonical palette/component/recolor/pack rule intact and varies only the episode-fixed ranking key:

- `occupied_area` — the exact canonical Racket program.
- `bbox_area` — descending bounding-box footprint, then occupied area and source bbox as tie-breaks.

The extension is **proposed and unapproved**. It does not change canonical generation, catalog status, or training admission.

From the packet extraction root, generate the retained three-demo/four-query evidence with the bundled Racket runtime:

```bash
python3 review.py run python3 generators/8bc2bc6a9bb8/workspace/parametric/prototype.py \
  --seed 37 --demos 3 --queries 4 \
  --out ../checks/parametric/8bc2bc6a9bb8-sort-key-final
```

Run the bounded adversarial surfaces with:

```bash
python3 review.py run python3 generators/8bc2bc6a9bb8/workspace/parametric/adversarial_probe.py \
  --out ../checks/parametric/8bc2bc6a9bb8-sort-key-probe-final.json
```

Public files contain demonstrations and query inputs only. Query answers, the hidden setting, seed, and Racket program remain private. `public_turn()` reveals one query at a time without total-count or final-turn metadata. For a fixed seed, setting, and demonstration count, the first turn is byte-for-byte identical to requesting a single query.
