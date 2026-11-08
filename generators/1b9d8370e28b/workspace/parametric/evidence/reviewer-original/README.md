# Proposed cyan-anchor prototype

This task-local prototype keeps the production generator and canonical Racket
authority separate. It varies one hidden transformation parameter once per
complete episode:

| Parameter | Values | Canonical/default |
|---|---|---|
| `cyan_anchor` | `left`, `right` | `left` |

Both settings preserve the original reasoning structure: infer the straight
cyan/blue split, count red cells independently in each row and region, erase
the original placements, and compact the same row counts to color-directed
edges. The alternative changes only the color-to-edge mapping: cyan moves right
and blue moves left. Input constraints do not depend on the setting. Every
selected-family input contains red cells in both regions and leaves background
visible in each affected row, so the two settings disagree and demonstrations
identify the hidden setting before the query.

From the extracted packet root, build fresh evidence with the included protected
Racket runtime:

```bash
python3 review.py run python3 \
  generators/1b9d8370e28b/workspace/parametric/verify.py \
  --out ../checks/parametric/cyan-anchor-v1 \
  --seeds 0 1
```

The output includes byte-exact Racket programs for both settings, canonical
replay for the default, complete private episodes, public challenge projections
with hidden settings and query answers removed, a same-input disagreement
witness, runtime identity, hashes, a report, and a manifest. Python mirrors are
used only as assertions; all retained labels are executed by Racket.

This is a **proposed, unapproved prototype**. It is not a production parametric
API, a new canonical rule, or a claim that these are the only plausible nearby
variants.
