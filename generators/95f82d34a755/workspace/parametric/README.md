# Native parametric family: 95f82d34a755

`in_place` is the selected canonical Racket source byte-for-byte.
`first_match_to_origin` first constructs the complete row-header/column-header
equality field, derives its first nonzero coordinate in row-major order, and
cyclically shifts the entire field by that input-derived coordinate.

The sampler is independent of the private setting, supports 3–6 demonstrations
and 1–4 prefix-stable queries, and guarantees that pre-anchor row and column
labels cannot match. Shared tails use three colors, making the field dense and
nontrivial. The first three demonstrations use anchors `(1,2)`, `(2,1)`, and
`(3,4)`, separating full two-axis alignment from one-axis and fixed-shift
shortcuts. Query four is a 30×30 input with a 29×29 equality field, first match
at `(8,9)`, at least 80 matches, and at least three match colors.

Reusable authoring checks from the packet root:

```bash
python3 review.py run python3 generators/95f82d34a755/workspace/parametric/audit.py \
  --seeds 20 \
  --out generators/95f82d34a755/workspace/parametric/evidence/current/self_audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 95f82d34a755 \
  --out ../checks/95f82d34a755/qualification --summary
```
