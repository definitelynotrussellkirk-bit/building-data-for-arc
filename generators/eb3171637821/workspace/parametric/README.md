# Parametric divider-lattice family

The native adapter exposes one finite parameter, `encoding`:

- `solid_count` is the byte-exact canonical program and returns a solid
  `row-band-count × column-band-count` rectangle in the cell color.
- `area_parity` detects and measures the same ordered bands, then colors each
  compressed cell by the parity of the corresponding source rectangle's area.

Inputs are deterministic for `(seed, split, index)` and identical across
settings. Episodes support 2–6 demonstrations and 1–4 queries. Every four-query
lesson includes one exact 30×30 stress lattice.

Run the task tests from the packet root:

```bash
python3 review.py task-tests eb3171637821 --phase after \
  --out ../checks/eb3171637821-tests
```

The review tool performs a bounded deterministic census and protected-Racket
spot checks; its conclusions apply only to the enumerated seeds and rivals:

```bash
python3 review.py run python3 \
  generators/eb3171637821/workspace/parametric/tools/review_family.py \
  --out generators/eb3171637821/workspace/parametric/evidence/current/family-review.json
```
