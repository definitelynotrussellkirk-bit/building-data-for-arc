# Authoring workspace for 1bfb2ef9ca71

The selected implementation is `../generator.py`; files here are reusable
source-bound diagnostics and are never selected automatically.

## Structural/curriculum probe

From `WORK/` through the bundled Racket/runtime wrapper:

```sh
python3 run_with_racket.py python3 generators/1bfb2ef9ca71/workspace/probe_generator.py \
  --seeds 64 --indices 8 --out ../checks/final-probe.json
```

The report binds the selected source hash and checks deterministic replay,
self-checks, orientation/height witnesses, every exact axis combination,
canonical mirror/rival behavior, and all query rotations of both declared
schedule residues. It uses the Python mirror only for diagnostics; Racket remains
label authority.

## Shortcut witness materializer

```sh
python3 run_with_racket.py python3 generators/1bfb2ef9ca71/workspace/materialize_counterexample.py \
  --out ../checks/fixed-height-counterexample/source.json
python3 run_with_racket.py python3 -m arcpuzzles apply 1bfb2ef9ca71 \
  --input ../checks/fixed-height-counterexample/input.json \
  --out ../checks/fixed-height-counterexample/racket.json
```

This regenerates seed 731 / sample index 1 / medium, where a four-row rectangle
separates the intended rule from the canonical-fitting fixed-height-three rival.
