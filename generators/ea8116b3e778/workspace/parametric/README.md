# Symmetry-mode prototype for `ea8116b3e778`

This is a task-local, **unapproved** extension. It does not modify or select
`generator.py`, the canonical Racket authority, or approval metadata.

## Parameter

One hidden `symmetry_mode` is fixed for a complete episode:

- `horizontal`: reflect red cells across the pivot's horizontal center axis.
- `vertical`: reflect red cells across the pivot's vertical center axis.
- `half_turn`: reflect red cells through the pivot center.
- `both`: apply all three mirrors. This is the exact canonical default.

Every retained input uses the production generator's lawful
`single_quadrant` profile. The same source inputs are reused across all four
settings, so output changes are caused by the rule parameter rather than a
sampler change. Each demonstration and query separates the selected setting
from every declared rival. Demonstration and query counts are independent;
the retained batch uses two demonstrations and four distinct queries.

## Files

- `prototype.py`: sampler, Python mirrors, exact setting-specific Racket,
  episode validation, and public/private writers.
- `verify.py`: runs every retained pair through all four Racket programs,
  checks Python/Racket parity and rival disagreement, then materializes
  answer-free public challenges plus private episodes/programs.
- `materialized/`: generated replay artifacts; public filenames are SHA-256 of
  the exact visible bytes and reveal neither setting nor query answers. Hidden
  metadata and private query labels cannot change public IDs, retained public IDs
  are sorted, and verifier cleanup touches only its own generated paths.

## Replay

From the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/ea8116b3e778/tests/test_parametric_symmetry_mode.py -q

python3 review.py run python3 \
  generators/ea8116b3e778/workspace/parametric/verify.py \
  --seed 53 --demonstrations 2 --queries 4 \
  --out ../checks/parametric/ea8116b3e778-symmetry-mode.json \
  --artifact-dir generators/ea8116b3e778/workspace/parametric/materialized
```

Generate a single private/public pair directly:

```bash
python3 review.py run python3 \
  generators/ea8116b3e778/workspace/parametric/prototype.py \
  --seed 53 --symmetry-mode vertical --demonstrations 2 --queries 4 \
  --private-out generators/ea8116b3e778/workspace/parametric/example-private.json \
  --public-dir generators/ea8116b3e778/workspace/parametric/example-public
```
