# Matched completion-footprint variants

This task-local prototype keeps dense gray camouflage and incomplete yellow
fragments, while varying the episode-fixed footprint that each fragment
completes:

- `cardinal` (canonical): center plus the four axial neighbors.
- `diagonal`: center plus the four diagonal neighbors.

Every input is deliberately valid under both candidate programs. A two-yellow
motif has one cardinal interpretation and one shifted diagonal interpretation;
the union of both five-cell footprints is gray/yellow. Therefore the private
setting is not visible from the sampler, and the demonstrations must identify it
from executed outputs. The canonical Racket file is byte-for-byte the selected
authority. This proposal does not grant variant acceptance or training admission.

`adapter.generate(seed, settings, demos=3, queries=4)` supports exact seeds in
`0..2**63-1`, 2–6 demonstrations, and 1–4 queries independently. Query prefixes
are stable, all inputs are distinct, and both settings use identical inputs.
The four ordinary queries reach 11×13, 17×19, 24×26, and 30×30. The 30×30 case
contains eight spread motifs plus dense camouflage in all quadrants; it is not a
padded small scene.

Run focused verification from the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/1314f4ccf5cc/tests/test_parametric.py
```

The tests execute labels through the protected Racket worker, require the chosen
setting to be the sole survivor from demonstrations alone, exercise every demo
count, verify four-query sequential-prefix behavior, and reject malformed
controls. See `evidence/current/` for retained bounded results.
