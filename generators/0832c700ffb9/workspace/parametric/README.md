# Proposed ring-partner-axis prototype

This task-local prototype keeps the selected production generator and canonical
Racket authority unchanged. It varies one hidden rule parameter once per episode:

| Parameter | Values | Canonical/default |
|---|---|---|
| `ring_partner_axis` | `row`, `column` | `row` |

Both settings preserve the original reasoning structure: identify rectangle
corner dots, find an aligned partner, copy that partner's color into the clipped
3×3 ring, and draw the same color-5 guides. Only the partner axis changes.
Every selected-family input has exactly one row and one column partner per dot.
Diagonal-color rectangles intentionally agree under both settings; existing
same-row-color rectangles distinguish them. The ordinary six-pair schedule has
four distinguishing pairs, so every five-demonstration single-query rotation
refutes the alternative setting.

From the extracted packet root, build fresh Racket-backed evidence with:

```bash
python3 review.py run python3 \
  generators/0832c700ffb9/workspace/parametric/verify.py \
  --out ../checks/parametric/ring-partner-axis-v1 \
  --seeds 8
```

The output contains exact Racket programs, private labelled episodes, public
challenge projections with hidden settings and query answers removed, one
same-input setting witness, execution receipts, hashes, a report, and a manifest.
The `row` program is required to be byte-exact canonical. All retained labels are
executed by the included Racket verifier and compared with the Python assertion
mirror.

This is a **proposed prototype**, not production integration, approval, or a
claim that row/column are the only plausible nearby rules. Canonical examples
alone are axis-ambiguous; teachability depends on the selected generator's
same-row-color rectangles and deterministic schedule.
