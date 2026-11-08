# 01023c69fe3c native parametric family

- `mode=canonical` preserves the canonical program byte-for-byte.
- `mode=interior_cue` builds the canonical crosshair/interior grid, reads the
  unique colored cell selected by the derived blue interior, and restores remote
  cells of that input color as azure.
- The sampler is setting-neutral, supports 2–6 demonstrations and 1–4 stored
  queries, and its normal four-query bank includes a substantive 30×30 scene.
- `wrong_intermediate_program()` is the retained causal counterfactual: it
  expands the selector by one cell and therefore reads the ring decoy.

Focused test:

```sh
python3 review.py run python3 -m pytest -q generators/01023c69fe3c/tests
```

Bounded adversarial audit (from `WORK/repo` through the packet wrapper):

```sh
python3 ../review.py run python3 generators/01023c69fe3c/workspace/parametric/adversarial_probe.py \
  --out generators/01023c69fe3c/workspace/parametric/evidence/adversarial.json
```
