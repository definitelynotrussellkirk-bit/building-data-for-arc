# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, prior solve notes, or audit records. I used only the public grids
in `challenge.json`/`README.md` and local Python over those grids.

## Revision 1 — labelled shape copies

### Observation and hypothesis

Each input contains several disconnected color-1 shapes plus three isolated
non-1 cells. Every isolated color is positioned to the right of one color-1
shape and shares a row with it. That nearby shape remains color 1 in the output.
Every other color-1 component with exactly the same translated shape (without
rotation or reflection) changes to the isolated marker's color. Components of
other shapes and the marker cells themselves remain unchanged.

The repeated-shape evidence is consistent across all three demonstrations:

- Example 0 uses three distinct five-cell shapes. The exemplars next to markers
  4, 5, and 7 stay blue; respectively matching copies become 4, 5, and 7.
- Example 1 again distinguishes three orientation-sensitive five-cell shapes.
  A rotated/reflected-looking shape is not conflated with a different signature.
- Example 2 repeats the same mechanism with three-cell shapes, showing that the
  rule is about component geometry rather than a fixed object size.

A pure nearest-component rule has an avoidable ambiguity in example 0: marker 7
is equally far in Manhattan distance from a vertical-nearby component and its
actual exemplar. The reliable visible relation is instead "nearest component to
the left on the marker's row," so the implementation uses that relation first.

### Implementation

1. Extract all 4-connected components of color 1.
2. Normalize each component by subtracting its top and left coordinates; keep
   orientation unchanged.
3. For each non-0/non-1 marker, select the closest component cell to its left on
   the same row and bind that component's normalized shape to the marker color.
4. Recolor every other component with that exact signature, leaving each labelled
   exemplar and every marker untouched.

### Predicted query behavior

For query 0, the second vertical triplet should become 6, the other horizontal
triplet should become 5, and both other copies of the `11/10` corner should
become 4. For query 1, the second vertical triplet should become 5, the other
`11/01` corner should become 3, and the other horizontal triplet should become 8.

### Remaining uncertainty

The demonstrations do not show two markers labelling the same shape signature,
a marker placed left/above/below its exemplar, diagonal connectivity, or a
non-marker color component. The solver follows the demonstrated same-row,
marker-to-the-right contract and has a Manhattan fallback only to remain total.
