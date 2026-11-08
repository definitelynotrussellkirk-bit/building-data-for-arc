# Solve work log

## Prior exposure

Before this blind solve I had not opened task `df5e596e5e96`'s generator, rule,
notes, solutions, audit records, or private labels. I had only read the packet's
general instructions and the visible `challenge.json` presentation produced by
`solve_episode.py blind prepare`.

## Visible structure and hypothesis

Every input is 5x29 and decomposes into five 5x5 panels separated by one all-zero
column. Each panel contains a single monochrome silhouette. Every output is a
symmetric 5x5 matrix with color 8 on the diagonal, suggesting pairwise relations
between the five silhouettes.

I converted each silhouette to the set of its occupied coordinates and removed
translation by subtracting its minimum row and column. Across the demonstrations:

- output 1 pairs have identical normalized coordinates (same orientation),
- output 2 pairs match after a proper 90/180/270-degree rotation,
- output 3 pairs match only after a reflection, possibly followed by rotation,
- output 0 pairs are not congruent under any dihedral transform.

The examples with different source colors show that color is irrelevant; occupancy
geometry is the signal. The diagonal 8 denotes self-comparison.

## Probe

I manually segmented the demonstrations, normalized each occupied-cell set, and
compared all eight square symmetries. This classification reproduces every visible
output entry in all three training examples. I therefore implemented that rule
with precedence: unchanged orientation (1), proper rotation (2), reflected
orientation (3), unrelated (0); diagonal entries are 8.

## Remaining uncertainty

A silhouette with internal symmetry can satisfy more than one transform class.
The demonstrations do not expose an ambiguous symmetric pair. The implementation
uses the natural precedence above so an unchanged orientation remains class 1,
then a proper rotation, then reflection.
