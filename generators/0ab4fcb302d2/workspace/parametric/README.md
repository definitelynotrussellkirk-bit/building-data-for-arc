# Proposed diagonal-code parametric prototype

Status: **proposed / unapproved**. This directory does not change the production
generator API, canonical approval, or canonical default rule.

The prototype varies two small, episode-fixed rule parameters:

- `diagonal_mapping`: `match` keeps the canonical mapping (a marker on the
  local main diagonal selects main-diagonal output blocks); `opposite` inverts
  that mapping.
- `block_size`: `4` is canonical and produces a 9x9 output; `3` produces a 7x7
  output while retaining the one-cell row and column gutters.

The default setting (`match`, `4`) is byte-for-byte the pinned canonical Racket
program. Inputs are independent of the selected parameters. Labels and all
parameter-rival predictions are produced by executing the materialized Racket
program with the included bridge, not by a Python answer mirror. Public files
contain three demonstrations and one unlabeled query; private files retain the
seed, parameter setting, exact rule text/hash, query label, and rival evidence.

From `WORK/repo`, run the focused tests:

```bash
python3 ../../review.py run python3 -m pytest -q \
  generators/0ab4fcb302d2/tests/test_parametric_variant.py
```

From the packet root, retain a four-setting evidence set under checks:

```bash
python3 review.py run python3 \
  generators/0ab4fcb302d2/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 \
  --out ../checks/parametric/episodes-v1
```

The evidence writer is intentionally no-overwrite: a repeated run must use a
new output directory or remove an explicitly disposable prior run first.
