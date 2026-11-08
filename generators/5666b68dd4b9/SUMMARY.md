# 5666b68dd4b9 — Keyed Frame Insert

The top-left cell selects a body color and the top-right cell selects a transform: `1` clockwise, `2` 180°, `3` left-right flip, and `4` the canonical identity fallback. Crop all selected-color body cells to their tight bounding box, transform the crop, clear the output, redraw the unique hollow color-8 frame, and transparently center the crop in its interior using the canonical floor-half placement.

Kind: `per_puzzle`. Reviewed generator version: `2.0.0`. Rule hash: `5a2705a2ea24`.

Normal lessons contain four demonstrations with one selector/source shape and codes `1..4`. A larger wrong-color object and optional frame-interior noise make largest-object, selector/code lookup, fixed-transform, and preserve-interior shortcuts falsifiable.

Review status: full local battery 12/12 green; protected Racket mirror parity 120/120; semantic strict census 600/600; focused tests 8/8.
