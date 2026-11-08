# 151f4dc0c08f native parametric family

`matrix_rule=pair_alignment` is the exact canonical source. The alternative
`anchor_component` builds the direct alignment graph, computes the connected
component containing the smallest-color marker, then renders that component as
an `N×N` cyan membership matrix. Every authored scene contains a transitive
chain and an isolated marker; the separate wrong-direct-neighbors program is the
causal ablation.

Run focused checks from the packet root:

```sh
python3 review.py run python3 -m pytest -q generators/151f4dc0c08f/tests
python3 review.py run python3 generators/151f4dc0c08f/workspace/parametric/audit.py \
  --out generators/151f4dc0c08f/workspace/parametric/evidence/current/audit.json
```
