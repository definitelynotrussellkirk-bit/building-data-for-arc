# Workspace: fdffdd0bbde7

The selected implementation is `../generator.py`. These authoring tools are
source-bound and load that exact file with `reviewer_support`.

## Independent distribution and authority probe

`reference_probe.py` reparses grids independently, mirrors the rule without
calling generator internals, evaluates every rival declared by the selected
module, checks deterministic generation and isolated witnesses, optionally
compares sampled outputs with Racket, and can exhaust the full Cartesian exact
axis domain.

From the packet's outer extraction directory:

```bash
python3 review.py run python3 generators/fdffdd0bbde7/workspace/reference_probe.py \
  --per-band 1000 --racket --exhaustive-axes \
  --out ../checks/reference-final.json
```

## Counterexample builder

`build_counterexample.py` verifies that each selected canonical shortcut fits all
usable canonical pairs, then writes a deterministic generated witness on which
all declared rivals differ from the authoritative rule. It requires Racket by
default and never silently replaces authority with its Python mirror.

```bash
python3 review.py run python3 generators/fdffdd0bbde7/workspace/build_counterexample.py
```

The retained result is `../counterexamples/current-shortcut.json` with its
Racket receipt under `../counterexamples/current-shortcut/checks/`.

## Focused tests

```bash
python3 review.py run python3 -m pytest -q \
  generators/fdffdd0bbde7/tests/test_generator_fdffdd0bbde7.py
```

The tests cover the strict parser/validator, canonical parity, all exact axis
endpoints and joint combinations, deterministic output, declared rival fitness
on canonical pairs, bi-axial anchor variation, isolated witnesses, and the
counterexample builder.
