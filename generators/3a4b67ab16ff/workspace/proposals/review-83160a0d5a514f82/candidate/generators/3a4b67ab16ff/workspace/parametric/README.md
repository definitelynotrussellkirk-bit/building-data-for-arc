# Proposed `layer_order` prototype for `3a4b67ab16ff`

Status: **task-local proposal; not production-approved**. The selected generator and canonical Racket rule remain bound to ascending numeric color order.

The prototype keeps the original family structure: color 5 defines the restored gray rectangle, each other color defines one bounding box, and only that box's intersection with gray is filled. The episode chooses exactly one hidden setting:

- `ascending` — the exact canonical Racket program; higher numeric colors win overlaps.
- `descending` — the same complete program with only the final color traversal reversed; lower numeric colors win overlaps.

Inputs come only from the selected production generator's `overlap_priority` profile. Paired episode seeds share the same input sampling, so the hidden setting does not choose the grids. The default evidence build uses three labeled demonstrations and four distinct unlabeled public queries per setting. Private records retain query answers, both complete programs, and exact-Racket executions.

From the packet root, build fresh evidence with:

```bash
python3 review.py run python3 \
  generators/3a4b67ab16ff/workspace/parametric/prototype.py \
  --out ../checks/parametric/3a4b67ab16ff-layer-order-v1 \
  --seeds 0 1 --demo-count 3 --query-count 4
```

The destination must not already exist. Public files use opaque `challenge-<sha256>.json` names derived only from visible demonstration inputs/outputs and query inputs. Private files and `report.json` record the setting, query answers, runtime identity, source hashes, canonical replay, and split-extrema repair checks.
