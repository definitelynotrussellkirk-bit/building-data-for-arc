# Horizontal fill-policy parametric family

- `fill_policy=all_pairs` is the exact selected canonical Racket source.
- `fill_policy=top_span_threshold` finds the topmost row with exactly two blue endpoints, uses its endpoint span as an input-dependent threshold, then fills only exact-pair rows whose span is at least that threshold.

The sampler is setting-neutral, deterministic, matched across settings and prefix-stable. It supports 2–6 demonstrations and 1–4 queries; the four-query bank ends with a substantive 30×30 scene. Singleton and three-endpoint rows make the exact-pair filter observable.

From the repository root:

```bash
python -m pytest --import-mode=importlib -q generators/6af5c333e5c1/tests/test_parametric_fill_policy.py
python generators/6af5c333e5c1/workspace/parametric/audit.py \
  --out generators/6af5c333e5c1/workspace/parametric/evidence/current/self-audit.json
```

Protected Racket qualification and the source-bound causal witness remain the execution authorities.
