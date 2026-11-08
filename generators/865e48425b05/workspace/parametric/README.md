# Palette-mask layout policy

This native parametric family keeps the selected canonical rule as the exact
`horizontal` default and adds two nearby packing policies over the same inputs:

- `horizontal`: crop the color-1 mask and place recolored copies left-to-right.
- `vertical`: crop the mask and stack recolored copies top-to-bottom.
- `dominant_axis`: crop and measure the mask, then pack horizontally when the
  bbox is wider than tall and vertically when it is taller than wide.

The first two demonstrations are constructive: a wide mask in a tall canvas and
a tall mask in a wide canvas. Their output-axis signatures are respectively
`HH`, `VV`, and `HV`, uniquely identifying all three settings from demonstrations
alone. All sampled masks are non-square, irregular, connected, and use the
visible palette order. Four query profiles include a seed-varied 30x30 stress
case with a 12x14 or 14x12 mask touching the bottom and right boundaries.

For `dominant_axis`, the required sequential dependency is:

1. **A:** crop the color-1 mask and measure its bbox.
2. **Intermediate:** mask height, width, and dominant axis.
3. **B:** choose horizontal or vertical output geometry and pack the recolored
   copies along that axis.

Skipping A and always choosing horizontal changes the tall-mask result. The
bounded audit checks this counterfactual, all declared settings, and named
shortcut programs through protected Racket. Public turn 0 contains all
illustrations plus query 0; later turns contain only the current masked query.
