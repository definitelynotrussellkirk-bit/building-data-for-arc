# Proposed parametric extension: section measure and axis order

This task-local prototype leaves the selected production generator and canonical
Racket authority unchanged. It varies two nearby rule parameters, chosen once
per episode and reused for all three demonstrations and the query:

- `measure_mode`: `sections` (canonical/default: separator count + 1) or
  `separators` (separator count directly);
- `axis_order`: `row_col` (canonical/default) or `col_row` (transpose the two
  measured counts when forming the output shape).

The object roles and reasoning path stay fixed: identify the strict-majority
background, identify the other color, count complete separator rows and columns,
form a fresh rectangular output, and fill it with the background color. The
selected generator's asymmetric count schedule makes all four combined settings
produce different output shapes on every retained pair.

The probe materializes all four exact Racket programs under `rules/`, builds one
complete episode for each setting, derives/checks every label through the packet's
Racket bridge, compares every pair against all three alternative settings, and
writes model-visible challenges without hidden parameters or query answers.

From the outer extracted packet, run:

```sh
python3 review.py run python3 generators/1c1ef857c9e2/workspace/parametric/prototype.py \
  --out ../checks/parametric/1c1ef857c9e2-section-axis-v1
```

The retained evidence is bounded to four deterministic seeds. It is a proposed
prototype, not production approval, training admission, or a proof against every
undeclared rule family.
