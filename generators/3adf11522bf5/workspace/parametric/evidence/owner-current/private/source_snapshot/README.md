# Proposed minimum disjoint-square side parameter

This isolated task-local prototype preserves the original square-detection and
disjointness reasoning while varying one hidden rule parameter once per complete
episode:

```text
minimum_disjoint_square_side = 2 | 3
```

`2` is the exact canonical/default behavior. Both settings find every globally
largest all-zero square, paint their union color 1, preserve the single obstacle
color, and then consider additional all-zero squares only when their complete
footprint is disjoint from the maximal union. The parameter changes only the
minimum side accepted by that final stage. On the selected side-2/side-3 input
manifold, setting `3` suppresses disjoint 2×2 regions while retaining the maximal
squares.

Each complete episode contains three demonstrations and one query under one
immutable setting. Its input schedule is parameter-independent: one `canonical2`
scene followed by three `teaching` scenes. The canonical-profile example is
invariant across settings; both teaching demonstrations refute the alternate
threshold before the teaching-profile query. Public JSON omits the threshold,
program, and query answer. Private evidence retains exact Racket programs and
hashes, all Racket-derived labels, source snapshots, seeds, and rival results.

Run from the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/3adf11522bf5/workspace/parametric/prototype.py \
  --seed-start 7300 \
  --out ../checks/parametric
```

Run the focused prototype tests with:

```bash
python3 review.py run python3 -m pytest -q \
  generators/3adf11522bf5/tests/test_parametric_minimum_square_side.py
```

This is a **proposed prototype** only. It does not change the selected production
generator, the canonical Racket authority, the rule hash, or approval status.

Public filenames are hashes of visible puzzle content, excluding private settings, seeds and query answers. Deliver only the public subtree; original reviewer sources and galleries are retained under `evidence/reviewer-original/`.
