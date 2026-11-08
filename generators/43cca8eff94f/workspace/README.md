# Task-local review workspace

The selected implementation is `../generator.py`; workspace files are never
automatically selected.

`reference_probe.py` is a portable, independent geometry oracle used by the
focused tests. It can:

- load either the selected generator or a path supplied through
  `GENERATOR_UNDER_TEST`,
- recover the five observable axes from pixels,
- execute a Python translation of the pinned slide-to-contact behavior, and
- execute the canonical-fitting `no_up` rival.

From the repository root:

```bash
PYTHONPATH=shared/runtime:generators/43cca8eff94f/workspace \
  python3 -c 'from reference_probe import load_generator,analyze; g=load_generator().generate(0,3); print(analyze(g))'
```

This helper is diagnostic only. Authoritative labels still come from the
selected Racket rule through the normal `arcpuzzles` runtime.
