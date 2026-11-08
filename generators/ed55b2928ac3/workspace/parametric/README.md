# ed55b2928ac3 parametric family

`finish_mode=plain` is the exact canonical rule. `finish_mode=top_edge_to_8` first performs the canonical keyed crop/transform (A), then reads the transformed top edge and recolors that selected color to 8 (B). The same input sampler is used for both settings.

Run focused checks:

```bash
python3 -m pytest -q generators/ed55b2928ac3/tests
python3 generators/ed55b2928ac3/workspace/parametric/adversarial_probe.py --out generators/ed55b2928ac3/workspace/parametric/evidence/current/self-review.json
```

`wrong-order.rkt` applies B before A and is retained for the protected causal witness.
