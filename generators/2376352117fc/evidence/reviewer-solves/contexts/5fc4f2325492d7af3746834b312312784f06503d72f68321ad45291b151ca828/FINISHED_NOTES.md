# Solve work log

## Exposure declaration before solving

I had not opened task `2376352117fc`'s generator, Racket rule, notes,
solutions, audits, or private labels.  I used only `challenge.json` and a local
visible-example test.  I had also not opened the assigned repair generator yet.

## Observation and hypothesis

Each input has a green shape (`3`) plus one blue marker (`1`) and one red marker
(`2`).  The output removes the original contents and redraws the green shape in
azure (`8`) after translating it by the vector from the blue marker to the red
marker.  Cells translated beyond the grid edge are clipped.

Coordinate checks on the visible pairs:

- Pair 1: blue `(5,1)` to red `(7,1)` gives shift `(+2,0)`; the green vertical
  line moves down two rows.
- Pair 2: blue `(4,1)` to red `(7,0)` gives shift `(+3,-1)`; one translated
  green cell falls off the left edge, matching the four visible azure cells.
- Pair 3: blue `(4,4)` to red `(9,4)` gives shift `(+5,0)`; the green line moves
  down five rows.

The two visible test inputs therefore predict a three-cell translated shape in
one case and a clipped five-cell vertical line at the left edge in the other.
No competing rule I considered fits all three training pairs as directly: using
the reverse vector fails every displacement, and moving the marker instead of
the shape fails the object-size preservation.

## Probe and implementation

I first ran a temporary local test over all three visible training examples
against the supplied `NotImplementedError` template; it failed for the expected
missing implementation.  I then implemented the translation, recoloring, blank
background, and boundary clipping in `solution.py`.

Remaining uncertainty is limited to whether colors are semantically fixed or
merely role-based in unseen data.  All visible examples use the same role colors,
so the solution follows that demonstrated contract rather than inventing a
palette-generalization unsupported by the episode.
