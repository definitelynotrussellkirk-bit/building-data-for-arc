# Native parametric prototype

`promotion.json` selects `adapter.py`, which delegates to the source-bound implementation in `native.py`. `canonical.rkt` is copied exactly from the selected catalog record. `largest_closure_dihedral.rkt` is the alternative program, and `first_object_dihedral.rkt` is its protected wrong-intermediate counterfactual.

The family parameter is `symmetry_closure`:

- `rotational_4`: complete every object under its four quarter-turn rotations.
- `largest_closure_dihedral`: first construct and measure every rotational closure; then select the unique largest closure and add only that object’s horizontal reflection.

`audit.py` performs bounded deterministic, teaching, shortcut-rival, projection, stress, base-repair, and protected-Racket checks. Canonical packet collection tests live in `../../tests/test_parametric_e685.py`.
