# Authoring workspace

The selected implementation is `../generator.py`; these utilities are never
automatically selected and must not be opened during a visible-only solve.

- `reproduce_counterexamples.py` regenerates the seed-23 witnesses, labels them
  through the selected Racket authority, and compares independently computed
  geometry ranks with the generator's actual declared rivals. The minimal saved
  grids are in `../counterexamples/`.
- `parametric/prototype.py` instantiates a proposed per-episode ascending/descending
  perimeter-order parameter, produces matching Racket programs, checks teaching
  evidence, and separates public challenges from authoring metadata. See its README.

Run authoring commands through the outer packet's `review.py run`; payload paths
are relative to `WORK/repo`. Use the exact recorded commands in the return's
`RESULTS.json` as historical receipts and adapt only the checkout/interpreter paths
when reproducing in a new environment.
