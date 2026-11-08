# 1713e09a3132 parametric family

`finish_mode=outline` is the exact canonical rectangle-border rule. `finish_mode=paint_enclosed` first renders all borders with canonical reading-order overwrite (A), then fills zero cells bounded by nonzero cells in all four cardinal directions with color 8 (B). B reads the combined rendered intermediate, including overlap collisions.

Run focused checks:

```bash
python3 -m pytest -q generators/1713e09a3132/tests
python3 generators/1713e09a3132/workspace/parametric/adversarial_probe.py --out generators/1713e09a3132/workspace/parametric/evidence/current/self-review.json
```

`wrong-order.rkt` applies the enclosure pass to sparse corners before rendering and is retained for the protected causal witness.
