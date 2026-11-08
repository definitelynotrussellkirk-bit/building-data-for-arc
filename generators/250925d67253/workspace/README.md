# Workspace

The selected implementation is `../generator.py`. This directory contains reusable authoring probes; drafts here are never automatically selected.

## Canonical-shortcut probe

`probe_shortcuts.py` scores every declared `CANONICAL_SHORTCUTS` rival against the portable canonical pairs, materializes one deterministic generated disagreement, and writes the input, Python mirror output, rival output, and source hashes. It intentionally does **not** call a private Racket runner; bind the witness to the public authority in a separate command.

From `WORK/`:

```bash
python3 run_with_racket.py python3 \
  generators/250925d67253/workspace/probe_shortcuts.py \
  --out-dir ../checks/generator-shortcut-replay

python3 run_with_racket.py python3 -m arcpuzzles apply 250925d67253 \
  --input ../checks/generator-shortcut-replay/input.json \
  --out ../checks/generator-shortcut-replay/racket.json
```

The probe refuses to overwrite an existing output directory. Defaults reproduce seed `0`, sample index `0`, difficulty `medium`, and overrides `mixed_fixed + dense + low`. Optional CLI controls select another seed/index and every declared generator axis.

The retained review evidence is under `checks/generator-shortcut-final/`; its public Racket output equals the Python mirror and differs from the bounding-box-center rival in 74 cells.
