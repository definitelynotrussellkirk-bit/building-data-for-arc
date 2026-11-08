# Review workspace for a8a8969ab4f1

The selected implementation is `../generator.py`. Files here are review tools,
not automatically selected generator code.

## `reference_probe.py`

Provides a source-selectable generator loader, public canonical-pair access,
pixel-only structural analysis, and an independent Python mirror of the prose
rule. Set `GENERATOR_UNDER_TEST=/path/to/generator.py` or pass a source path to
compare a retained candidate.

## `qualify.py`

Runs the task-specific checks that are deliberately broader than the shared
smoke battery:

```bash
python3 run_with_racket.py python3 \
  generators/a8a8969ab4f1/workspace/qualify.py \
  --starts-per-band 1000 --seed 404 --out ../checks/qualification.json
```

It tests every query rotation of overlapping four-pair windows, dynamically
scores all declared lesson competitors, verifies declared canonical shortcuts,
and exhausts every joint exact-axis combination in every difficulty band.
Generated labels use the independent mirror in `reference_probe.py`; the shared
battery and focused tests separately bind that mirror to canonical/Racket output.
