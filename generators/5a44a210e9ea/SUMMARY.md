# 5a44a210e9ea — ordered palette over valid frame components

Input row 0 is an ordered palette: read every nonzero colour from left to right, even when zero gaps separate entries. The remaining rows contain colour-1 components. A component is valid only when it is exactly the perimeter of its own bounding rectangle. Sort valid frames by bounding-box area, largest first, and paint them with palette colours by depth; if there are more frames than colours, reuse the final palette colour. Start the output as a zero grid, so every malformed blue component disappears, and omit the palette row.

Selected generator version: `3.0.0`. It pins canonical rule hash `8d815468fa81`, exposes five exact observable controls, and uses four schedule roles. The schedule redundantly demonstrates gapped palette parsing, final-colour reuse, and malformed-component rejection, including one combined stress example, so every leave-one-out query rotation retains evidence against each declared rival.

Kind: `per_puzzle`. Approval remains catalog-derived; this review does not admit training data.
