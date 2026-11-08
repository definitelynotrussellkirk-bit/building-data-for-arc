# Proposed line-axis parametric prototype

This task-local prototype keeps the selected production generator and canonical
Racket authority unchanged. It varies one hidden rule parameter once per episode:

| Parameter | Values | Canonical/default |
|---|---|---|
| `line_axis` | `row`, `column` | `row` |

Both settings preserve the original reasoning structure: select complete lines,
classify each line by whether all cells are identical, then paint that line gray
(`5`) or black (`0`). The alternative changes only the line orientation.
Controlled inputs contain exactly one uniform row and one uniform column, so every
pair distinguishes the settings while remaining lawful under the selected
canonical generator's input grammar.

From the extracted packet root, build fresh Racket-backed evidence with:

```bash
python3 review.py run python3 \
  generators/2a5919c40197/workspace/parametric/verify.py \
  --out ../checks/parametric/line-axis-v1 \
  --seeds 6
```

The output contains exact Racket programs, private labelled episodes, public
challenge projections with hidden settings and query answers removed, a
same-input setting witness, canonical-default replay, execution receipts, a
report, and a hash manifest. The `row` program must remain byte-exact canonical.
All retained labels are produced by the included Racket bridge and checked
against an independent Python assertion mirror. Every single-query rotation is
checked against the declared alternative axis.

This is a **proposed prototype**, not production integration, approval, or a
claim that row/column are the only plausible nearby rules. The bounded evidence
uses a controlled one-uniform-row/one-uniform-column family; broader scene
coverage and rivals outside the declared two-value parameter domain remain open.
