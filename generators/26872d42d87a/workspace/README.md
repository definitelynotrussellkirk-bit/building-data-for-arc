# Task-local workspace

The selected implementation is `../generator.py`. Workspace programs are review tools, not automatically selected generator code.

## Fast qualification census

Run from the repository root through the packet wrapper:

```sh
python3 review.py run python3 generators/26872d42d87a/workspace/qualify.py \
  --per-band 100 --seed 731 --out ../checks/qualification.json
```

`qualify.py` checks:

- all five labeled canonical pairs are accepted and reproduced by the Python mirror;
- each declared canonical shortcut really fits every labeled canonical pair;
- all five exact profiles are observed and honored in all three bands;
- every sampled input has both semantic witnesses and refutes both shortcuts;
- every 3-demo/1-query rotation is checked against all declared competitors; and
- all exact profile overrides are replayed in every band.

The default 100-per-band run produced 300 unique inputs, both witnesses in 300/300, both shortcut counterexamples in 300/300, and zero ambiguities across 1,200 rotations (`checks/qualification.json`). This is a fast source-only diagnostic. It does not execute Racket and does not prove identifiability against undeclared hypotheses; use the shared battery and `lesson-census` for source-bound Racket evidence.
