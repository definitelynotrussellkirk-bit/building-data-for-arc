# Solve work log

## Earlier exposure

I had not opened this task's generator, Racket rule, reference solutions, private
query labels, audit records, or prior solution explanations before this solve.
I only read the packet's visible presentation and `challenge.json`.

## Revision 1 — legend plus transform code

Observed structure in all three training inputs:

- Rows 0 and 1 contain a color legend in columns where both cells are nonzero.
  The row-0 colors are the pattern palette and the row-1 colors are their output
  replacements.
- A separate nonzero cell at `(0, 0)` acts as an operation code.
- The remaining nonzero cells below row 1 form a rectangularly cropped pattern.

Spatial probes against the three examples:

- code 4: rotating the crop 90 degrees counterclockwise, then applying the legend,
  exactly produces example 0;
- code 5: reflecting the crop left-to-right, then applying the legend, exactly
  produces example 1;
- code 3: rotating the crop 180 degrees, then applying the legend, exactly
  produces example 2.

Recoloring and the spatial transform commute, but the implementation performs the
spatial transform first and then recolors.  Background 0 remains 0.  The pattern
crop is the bounding box of nonzero cells below the two-row header, retaining any
zeros inside that box.

Alternatives considered: deriving the orientation from the pattern's position
relative to the header, or treating the first cell as another legend entry.  Those
interpretations do not consistently explain all three outputs, whereas the
single-pixel operation-code interpretation does.  Remaining uncertainty: only
one training example is supplied for each operation code, and unseen code colors
would be underdetermined.  Both visible queries use the demonstrated code 4.

Before implementation I ran the visible-pair harness against the supplied stub;
it failed with `NotImplementedError`, establishing the expected red test.
