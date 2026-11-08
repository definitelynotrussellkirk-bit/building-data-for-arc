# Ranked-anchor native parametric family

**Status: reviewer-qualified source candidate; owner acceptance pending.** The
production generator and canonical authority are unchanged. The default setting
returns the selected canonical Racket source byte-for-byte. Neither this source
candidate nor its generated episodes are admitted to training.

## Rule parameter

| `copy_policy` | Meaning |
| --- | --- |
| `all_anchors` | Canonical: discover the cyan-bearing prototype and copy it at its original origin and every external cyan anchor. |
| `signal_ranked_anchor` | Count the cells in the separate color-1 signal, use that count as a one-based rank among external cyan anchors in row-major order, and copy only at the original origin and selected anchor. |

The input sampler is independent of the private setting. It supports 2–6
demonstrations and exactly four independently generated, prefix-stable queries.
Query shapes are 15×17, 20×22, 25×27 and 30×30. The 30×30 scene has substantial
content and nonzero contact on all four boundaries. All pairs are distinct.

## Sequential dependency

- **Step A:** count the color-1 signal cells and bind the one-based rank.
- **Intermediate:** rank plus the row-major external-anchor inventory and selected anchor.
- **Step B:** overlay the discovered prototype at its origin and the selected anchor.
- **Why B depends on A:** the destination anchor cannot be known before the signal count is measured.

The retained protected-Racket witness replaces the measured rank with a wrong
rank on the same qualified input and changes the final output.

## Reproduce

From the packet’s outer directory:

```bash
python3 review.py run python3 -m pytest -q generators/75ff4423494a/tests
python3 review.py run python3 generators/75ff4423494a/workspace/parametric/audit_lessons.py \
  --seeds 64 --out generators/75ff4423494a/workspace/parametric/evidence/self_audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 75ff4423494a \
  --out ../checks/75ff4423494a/qualification --summary
```

The finite self-audit checks both declared settings, eight named shortcut rules,
matched inputs, demo-count boundaries, query-prefix stability, public projection,
and exact 30×30 coverage. It is not a universal uniqueness or learning proof.
