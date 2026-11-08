# Workspace

The selected implementation is `../generator.py`; workspace files are authoring tools and proposed variants, never automatically selected.

## Fast override preflight

Run from `WORK/` through the bundled runtime:

```bash
python3 run_with_racket.py python3 generators/3233860e2d81/workspace/probe_override_matrix.py \
  --seed 0 --sample-index 3 --out ../checks/override-preflight-final.json
```

The probe enumerates the shared checker's complete override-case set once in each difficulty band, verifies `self_check` and `observe_overrides`, and records undeclared rejections. It is a fast structural preflight, not a replacement for the full multi-seed battery.

## Parametric prototype

See `parametric/README.md` for the proposed episode-level `top_k ∈ {2,3,4}` extension and its public/private evidence boundary.
