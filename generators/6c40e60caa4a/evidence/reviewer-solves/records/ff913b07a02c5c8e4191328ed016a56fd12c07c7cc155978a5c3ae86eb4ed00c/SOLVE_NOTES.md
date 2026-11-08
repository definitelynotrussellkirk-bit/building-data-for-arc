# Solve work log

Earlier exposure: none to this task's generator, rule, reference program, private
labels, or prior solution explanations. I only read the packet's visible challenge.

## Revision 1 — packet baseline

The supplied `solution.py` raised `NotImplementedError`. I deliberately ran the
visible checker before implementation to establish a failing baseline; it reported
an execution error on all five visible examples.

## Revision 2 — smallest enclosing frame

Observed structure:

- Color 1 forms one or more rectangular outlines.
- Every color-2 marker lies strictly inside a rectangular outline.
- The output replaces the complete interior of the marker's *smallest* enclosing
  outline with color 3, preserving the color-1 border and all unrelated cells.
- This distinction matters for nested outlines: a marker in a 3×3 inner frame
  changes only its 1×1 interior, not the larger outer frame's interior.
- A 3×4 frame changes both cells in its 1×2 interior, showing that the operation
  is filling the selected interior rather than merely recoloring the marker.

Implementation probe: enumerate every axis-aligned box strictly enclosing each
marker, retain boxes whose full boundary is color 1, choose the smallest interior,
and fill that interior with 3. The search uses the original input for frame
recognition so earlier fills cannot affect later markers. It does not assume that
frames are isolated connected components, which also covers touching frames.

Remaining uncertainty: the visible data do not specify behavior for an unenclosed
marker. The implementation uses a total-function fallback that recolors such a
marker to 3; generated examples appear to make this branch unreachable.
