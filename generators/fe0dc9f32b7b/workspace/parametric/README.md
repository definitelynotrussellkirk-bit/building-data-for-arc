# `fe0dc9f32b7b` parametric family

This task-local family keeps the selected canonical rule byte-for-byte for
`palette_direction=outer_to_inner`.  The sole alternate setting reverses the
palette before the unchanged component-classification, containment-depth, and
fill stages.

## Native interface

- `adapter.py`: exports `program(settings)` and
  `generate(seed, settings, demos, queries)`.
- `promotion.json`: finite two-setting contract; 2–6 demonstrations and exactly
  four distinct queries.
- `prototype.py`: deterministic sampler, Python mirror, public one-query turns,
  declared-rival audit, and the depth-clamping counterfactual used by the
  sequential-dependency witness.
- `build_evidence.py`: regenerates the bounded audit and public-payload hashes.

## Regenerate local evidence

From the repository root:

```bash
python generators/fe0dc9f32b7b/workspace/parametric/build_evidence.py \
  --out generators/fe0dc9f32b7b/workspace/parametric/evidence/current \
  --seed 0 --seed 17 --seed 83 --seed 991
```

The evidence sweep covers both settings, every supported demonstration count,
and four queries per episode.  It is a finite shortcut audit, not a proof over
arbitrary programs.  Protected-Racket qualification is recorded separately by
the review harness.
