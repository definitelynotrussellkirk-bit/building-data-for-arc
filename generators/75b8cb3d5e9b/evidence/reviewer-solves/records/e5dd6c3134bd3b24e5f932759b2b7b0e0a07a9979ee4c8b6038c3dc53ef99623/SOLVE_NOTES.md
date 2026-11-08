# Visible-only solve notes

Earlier exposure: yes — I repaired this generator before this episode. During this solve I consulted only `solve/challenge.json`, not the generator or Racket rule.

## Hypothesis

The two full color-9 columns divide each input into source, transformed-source, and query panels. Crop each panel to its nonzero/non-9 bounding box. Infer which of the eight square dihedral transforms maps the first crop exactly to the second, using a fixed enumeration when more than one matches, and apply that same transform to the query crop.

Train example 1 is an explicit clockwise rotation: the source crop `666/060/006` becomes `006/066/606`; rotating the query crop clockwise gives the supplied output. The other visible examples use the same transfer pattern with different orientations.

## Implementation plan

1. Find exactly two full-height columns of 9 and split around them.
2. Crop each panel to its motif.
3. Enumerate identity, clockwise/180/counterclockwise rotations, left-right flip, and the three remaining reflected orientations.
4. Return the query transformed by the first code that maps source to target.
