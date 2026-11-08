# Composition-order prototype (proposed, not canonical)

This task-local prototype holds the generator's object-selection rule and input
distribution fixed while varying one small rule parameter once per episode:

| Parameter | Values | Canonical/default |
| --- | --- | --- |
| `composition_order` | `forward`, `reverse` | `forward` |

`forward` applies the two header transforms as `step1` then `step2`; `reverse`
applies `step2` then `step1`.  The script searches only for a lawful generated
4-demo/1-query episode where actual outputs under the two settings differ in at
least one demonstration and in the query.  It then runs both exact Racket
programs through the included bridge, verifies them against the task-local
mirrors, and writes public/private evidence separately.  Public files omit the
hidden parameter, both programs, and query answers.

From the packet extraction directory, run:

```bash
python3 review.py run python3 generators/72416068b0cf/workspace/parametric/prototype.py \
  --seeds 2 0 --difficulty easy \
  --out-dir ../checks/parametric/order-prototype
```

The chosen seeds deterministically cover both settings (`2` -> canonical
`forward`, `0` -> proposed `reverse`).  This is bounded prototype evidence, not
approval of a production parametric API or a change to the selected canonical
rule.
