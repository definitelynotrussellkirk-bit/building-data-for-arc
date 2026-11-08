# Workspace: 8118155d8959

The selected implementation is `../generator.py`. Workspace files are support tools, not automatically selected generators.

## Shortcut probe

`shortcut_probe.py` is a source-bound maintenance probe. It:

1. checks every declared `CANONICAL_SHORTCUTS` rule against all usable canonical pairs;
2. counts generated disagreements for every current `SEMANTIC_RIVALS` entry; and
3. checks complete consecutive three-demonstration windows against every current `LESSON_COMPETITORS` entry.

Run from the repository root:

```sh
PYTHONPATH=shared/runtime:src python3 \
  generators/8118155d8959/workspace/shortcut_probe.py \
  --per-band 100 --lesson-starts 100 \
  --out ../checks/shortcut-probe-final.json
```

The high-volume generated census uses the checked-in Python mirror. For an official output, save a reported counterexample input and run the supported Racket-backed command:

```sh
python3 ../run_with_racket.py python3 -m arcpuzzles apply 8118155d8959 \
  --input ../checks/shortcut-witness-final/input.json \
  --out ../checks/shortcut-witness-final/racket.json
```

The final retained report is bound to generator SHA-256 `ab6964be99e6f3a6084621918dd1b5dcba7cbefbdf975043fbb1a259e7e4718f`.
