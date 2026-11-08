# Workspace for `f60cfd11346a`

The selected implementation is `../generator.py`. This workspace contains reusable review tooling, not an alternate selected generator.

## `reference_probe.py`

Source-bound probe that:

1. loads every rival declared in `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`;
2. checks each against all usable canonical pairs;
3. generates the exact retained witness (`seed=43`, `sample_index=2`, medium, 9×11 vertical, accent 1);
4. samples 64 ordinary draws and counts rival disagreements;
5. optionally calls the supported selected-Racket apply path and verifies rule/hash/output parity.

Run from the packet's `WORK/` directory:

```bash
python3 run_with_racket.py python3 \
  repo/generators/f60cfd11346a/workspace/reference_probe.py \
  --out checks/shortcut-witness-v310/probe.json \
  --with-racket
```

The final retained receipt is `checks/shortcut-witness-v310/probe.json`, bound to generator SHA `c8b8f277bb56e95db13d75c843bb89e210be443b95cab51bae299a576bcc14eb` and rule hash `23823efe5a14`.
