# Workspace

The selected implementation is `../generator.py`. Workspace files are reviewer tools and are never automatically selected.

## `reference_probe.py`

A portable, independent task-domain probe used by the focused tests. It provides:

- an independent exact-parity oracle;
- executable plausible rivals;
- morphology/component measurements;
- portable canonical-pair access through `reviewer_support.find_root` / `canonical_pairs`.

It intentionally does not import the selected generator's private rule implementation. Use it for future regression tests or curriculum checks; generated labels remain owned by the selected Racket authority.
