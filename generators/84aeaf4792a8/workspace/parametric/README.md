# Equivalence-policy parametric family

`rotation` is the byte-exact selected canonical rule. `dihedral` uses the same
component extraction, reading order and relation-matrix rendering but also
allows reflections when assigning shape-equivalence classes.

Sequential dependency:

1. **A:** extract ordered monochromatic components and compute each component's
   input-dependent canonical orbit key under the selected transformation group.
2. **Intermediate:** the ordered orbit-key/class vector.
3. **B:** render the N×N matrix from equality of those keys (5 diagonal, 8 equal,
   0 otherwise). The matrix cannot be selected before the class vector exists.

`audit.py` performs protected-Racket parity, finite-rival learnability checks and
privacy-safe one-query-per-turn export. `counterfactual_bbox.rkt` replaces the
orbit intermediate with area/bounding-box statistics for the causal witness.
