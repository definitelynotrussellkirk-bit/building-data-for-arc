# Parametric metric/direction prototype

This opt-in family preserves the source task's full reasoning pipeline: discover
nonzero 4-connected components, measure each component, infer the episode-fixed
sort rule from demonstrations, crop every component, and gallery-pack the crops.
The two small parameters are `metric = perimeter|area` and
`direction = descending|ascending`; the exact canonical default is
`perimeter/descending`.

`adapter.py` is the native promotion-v1 interface. `prototype.py` supplies
matched deterministic inputs, 2–6 demonstrations, a stable prefix of up to four
queries, protected-Racket evidence, demonstration-only finite-rival teaching
certificates, and strict public/private materialization. The third query is a
substantive 30×30 six-object boundary case (76 nonzero cells), not padded small
content. Public IDs hash only exact `reviewer_support.public_challenge_bytes`.

Example through the packet launcher:

```bash
python3 review.py run python3 generators/7e52d15790d7/workspace/parametric/prototype.py \
  materialize --seed 17 --demos 3 --queries 4 \
  --out generators/7e52d15790d7/workspace/parametric/evidence/current/batch
python3 review.py run python3 generators/7e52d15790d7/workspace/parametric/prototype.py \
  verify generators/7e52d15790d7/workspace/parametric/evidence/current/batch \
  --report generators/7e52d15790d7/workspace/parametric/evidence/current/verification.json
```

This is proposed evidence only. Owner qualification/acceptance and downstream
training admission remain separate.
