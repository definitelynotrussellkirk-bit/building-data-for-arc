# Solve work log

## Exposure boundary

Before this blind solve I had not opened task `20859a33c80e`'s generator, Racket rule,
reference solutions, private query labels, audit records, or prior solution notes. I had
only read the packet-level instructions and the visible examples produced by
`python3 solve_episode.py blind prepare`.

## Revision 1 hypothesis

The transformation preserves the grid and background, but normalizes every nonzero
cell according to spatial nesting rather than its input color.

I treated each 4-connected same-color nonzero group as a component. For each component
I computed its inclusive bounding box. A cell's output is `2 + k`, where `k` is the
number of *other* component bounding boxes containing that coordinate. The component
that owns the cell is excluded.

This explains all visible edge cases:

- outer frames/L-shaped scaffolds have depth 0 and become color 2;
- inner frames and markers inside one larger box become color 3;
- the center inside two nested boxes becomes color 4;
- train 2's different-color cell replacing an outer-frame corner is inside the outer
  component's inferred bounding box and therefore becomes 3;
- train 3's isolated color-2 cell is disconnected from the large color-2 L, lies inside
  the L component's bounding box, and therefore becomes 3;
- side-by-side frames do not contain one another, so both remain depth 0.

I tested this candidate in a throwaway script against all five visible training pairs;
it matched every output exactly. Remaining uncertainty: the examples do not distinguish
inclusive bounding-box containment from a more semantic notion of inferred enclosure,
but the corner replacement and open L examples strongly favor inclusive component boxes.

## Revision 1 result

`python3 solve_episode.py blind check --intent solve ...` completed and passed all
5/5 visible examples. I made no further revisions because the hypothesis already
covered every demonstrated special case with one consistent rule. Query correctness
remains masked by design.
