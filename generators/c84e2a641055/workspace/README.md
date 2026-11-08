# Review workspace

`review_probe.py` is a fast, source-bound development probe for this task. It:

- verifies every declared `CANONICAL_SHORTCUTS` rule against all labeled public pairs;
- searches the production sampler for an exact input where each shortcut disagrees;
- checks every single-pair query rotation for consecutive lesson windows and all declared competitors;
- records the final generator SHA-256, rule hash, seed, axes, grids, and rival outputs in JSON.

Run from the packet root through the supplied runtime wrapper:

```sh
python3 run_with_racket.py python3 generators/c84e2a641055/workspace/review_probe.py \
  --seed 7300 --starts 16 --out ../checks/review-probe.json
```

The probe uses `generator.rule_mirror` for speed. It is not an authority substitute;
confirm report claims with `arcpuzzles apply`, the semantic gate, and the Racket-backed
lesson census.
