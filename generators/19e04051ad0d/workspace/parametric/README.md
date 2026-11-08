# Proposed cycle-direction parameter (isolated prototype)

This prototype preserves the original three-region reasoning pattern and varies
one hidden rule parameter once per complete episode:

```text
cycle_direction = next | previous
```

`next` is the original/default setting and uses the exact canonical Racket
program for task `19e04051ad0d`. `previous` changes only the cyclic region index
from `(remainder (+ i 1) n)` to `(remainder (+ i (- n 1)) n)`. Both settings
still require the solver to infer the modal background, full-background
separator columns, region boundaries, and one foreground color per region.

Each complete episode contains three demonstrations and one query under one
immutable setting. Every selected-generator input has visible holes in all
three regions and three distinct region colors, so next and previous produce
different outputs on every pair. Public challenge JSON retains demonstrations
and the query input but omits the parameter value, Racket program, and query
output. Private evidence retains exact programs/hashes, selected-generator
source hash, Racket-derived outputs, seeds, and rival checks.

Run from the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/19e04051ad0d/workspace/parametric/prototype.py \
  --out ../checks/parametric
```

This is an isolated proposal only. It does not alter the selected production
generator, canonical authority, or current training approval. The
`previous` setting is a proposed sibling rule rather than a claim about the
original ARC family.
