# Task-local qualification workspace

`qualify.py` is the reusable final-source probe for this generator. It derives
rivals and shortcuts from the generator declarations instead of duplicating a
name list, checks every cyclic schedule start and every query rotation, verifies
canonical labels, counts distribution support, records the generator SHA-256,
and can compare generated labels against the selected Racket authority.

From the extracted packet root:

```bash
python3 review.py run python3 generators/bfef8519fe18/workspace/qualify.py \
  --per-band 32 --racket --racket-samples 24 \
  --out ../checks/bfef8519fe18_qualification.json
```

The script exits nonzero for rejected canonical inputs, missing declared-layout
support, no-op generation, canonical shortcuts without counterexamples,
ambiguous production lessons or query rotations, or Racket/Python disagreement.
