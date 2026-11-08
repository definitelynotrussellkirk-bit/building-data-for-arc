# Matched room-extreme variants

This task-local prototype varies one episode-fixed decision while holding every
input constant across settings:

- `minimum` (canonical): color every smallest 4-connected zero room `3` and
  every other zero room `4`.
- `maximum`: color every largest 4-connected zero room `3` and every other zero
  room `4`.

The first demonstration is an intact unequal lattice, so room area is not
confounded with a broken wall. The second includes an opened separator and
reuses absolute room areas from the first while changing which area is extreme.
Together the minimum two demonstrations defeat both the known “opened wall means
large” shortcut and a fixed absolute-area shortcut. Later profiles add multiple
openings, rectangular aspect ratios, boundary rooms, and an exact 30×30 stress
scene. Sampling depends only on `(task, seed, split, index)`, never on the hidden
setting or requested prefix length.

`adapter.generate(seed, settings, demos=3, queries=4)` accepts exact seeds in
`0..2**63-1`, 2–6 demonstrations, and 1–4 queries independently. All episode
inputs are distinct, query prefixes are stable, and the two settings receive
identical inputs. The canonical Racket file is byte-for-byte the selected
catalog authority. Python labels remain authoring claims until native
qualification executes every pair through protected Racket. This proposal does
not grant variant acceptance or training admission.

Run focused verification from the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/953db766893d/tests/test_parametric_extreme.py
```
