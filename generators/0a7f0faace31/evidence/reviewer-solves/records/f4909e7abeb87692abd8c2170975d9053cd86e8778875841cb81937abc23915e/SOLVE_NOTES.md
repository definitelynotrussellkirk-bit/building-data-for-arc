# Visible-only solve notes

The three demonstrations share a background color 5 and sparse color-7
markers.  Taking the bounding box of all 7-cells gives a rectangular guide.
The output is not a mask: it is an exact rectangular crop from the input, so
background cells and any differently colored cells enclosed by the selected
shape remain in place.

I considered each monochrome 4-connected component other than colors 5 and 7
in row-major order.  In every demonstration, the output is the crop around the
first component whose own bounding-box midpoint (using floor division) lies
inside the color-7 guide box.  Earlier components lie outside the guide.  The
implementation follows exactly that rule and stops after matching all three
visible demonstrations.

No private query output was inspected, and no reference implementation or
rule file was consulted after this solve episode was prepared.  Prior work on
the assigned generator is disclosed separately by the solve-finish metadata.
