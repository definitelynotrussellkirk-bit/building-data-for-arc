# Proposed bounding-box halo-radius parameter (non-production)

This task-local prototype keeps the original reasoning sequence intact: find
cardinally connected red components, ignore red singletons, compute each
multi-cell component’s bounding box, expand it, clip to the canvas, and paint
only black cells green. The sole proposed rule parameter is
`halo_radius ∈ {1,2}`. Radius `1` returns the exact canonical Racket program;
radius `2` changes only the expansion distance. One hidden radius is selected
once per episode and remains fixed across three demonstrations and one query.

Prototype inputs contain a multi-cell red component at least two cells from all
edges plus isolated red singleton contrast objects outside its radius-two box.
Every retained pair therefore distinguishes both settings. This is deliberately
a bounded authoring domain, not a proposed restriction on the canonical task.

From the outer extracted packet directory, run:

```bash
python3 review.py run python3 \
  generators/7185b8225f1c/workspace/parametric/prototype.py \
  --base-seed 20261020 \
  --out ../checks/parametric/halo-radius-v1
```

The command executes both exact Racket programs through
`arc_repl.isolated_verifier.verify_candidate`, cross-checks every result against
an independent Python mirror, retains one complete episode per radius, and
checks all four query rotations against the alternate setting. Public episode
JSON contains three labeled demonstrations and one unlabeled query only; hidden
parameters, Racket source, and query answers remain in private evidence.

This is **proposed prototype evidence only**. It does not alter `generator.py`,
the canonical rule authority, catalog metadata, or training approval.
