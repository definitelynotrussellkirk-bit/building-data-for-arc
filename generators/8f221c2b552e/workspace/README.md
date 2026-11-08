# Review workspace for `8f221c2b552e`

The selected implementation is `../generator.py`; files here are independent review tools and are not imported by production generation.

- `reference_probe.py` provides a pixel-derived axis parser, an independent row-bridge oracle, canonical-pair loading, cyclic lesson/query rotations, and real-Racket batch parity. Racket parity deliberately has no Python fallback.
- `qualification.py` emits a machine-readable qualification report. It checks canonical acceptance, determinism, independent axis observability, exact override round trips, every query rotation of cyclic four-example windows, declared-rival refutation, and optional selected-Racket parity.

Full review command:

```bash
python3 -B generators/8f221c2b552e/workspace/qualification.py \
  --samples-per-band 100 --starts-per-band 100 --racket-samples 60 \
  --out ../checks/qualification.json
```

Use `--generator PATH` to qualify a copied/replayed source. Use `--skip-racket` only for a deliberately local smoke test; the resulting report records that parity was skipped.
