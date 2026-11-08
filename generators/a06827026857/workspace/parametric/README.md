# Native window-scope family

The family preserves the selected canonical rule exactly as `window_scope=all_windows`.
Both settings first enumerate solid monochrome nonzero 3x3 windows from the original
input. `dominant_color` then binds the unique color with the largest number of
qualifying windows and paints only that color's window corners. The retained
`wrong_first_color.rkt` witness substitutes the color of the first row-major window,
which the ordinary lessons deliberately make a decoy.

Focused checks:

```bash
cd WORK/repo
/opt/pyvenv/bin/python3 -m pytest -q generators/a06827026857/tests
/opt/pyvenv/bin/python3 generators/a06827026857/workspace/parametric/audit.py \
  --out generators/a06827026857/workspace/parametric/evidence/current/audit.json
```

Native qualification, protected Racket replay, public projection, and causal witness
are packet-level gates; this README does not claim owner acceptance or training admission.
