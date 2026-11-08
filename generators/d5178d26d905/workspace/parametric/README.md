# Proposed `special_mapping_order` prototype

This task-local prototype preserves the canonical template/reference parsing,
line colors, fill colors, retention masks, and output geometry. It varies only
the order that associates template special rows with reference special rows:

- `top_to_bottom` — canonical/default setting; reference rows are used in their
  natural top-to-bottom order.
- `bottom_to_top` — proposed alternative; the same reference rows are reversed
  before mapping the unchanged template variants.

One value is selected once from the episode seed and reused for all three
training pairs and the query. Every retained demonstration has three distinct
special variants and is required to produce different outputs under the two
exact Racket programs. Public files omit the setting, rule text, and query
answer. This is a proposed prototype only; it does not alter or approve the
selected canonical production rule.

From the outer packet directory:

```sh
python3 review.py run python3 \
  generators/d5178d26d905/workspace/parametric/prototype.py \
  --seed 23 --out ../checks/parametric/d5178d26d905-mapping-order
```

Focused checks:

```sh
python3 review.py run python3 -m pytest -q \
  generators/d5178d26d905/tests/test_parametric_mapping_order.py
```
