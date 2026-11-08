# df19226c9807

0-bg grid (h×w, ~10-18 by ~13-22) with THREE CORNER ANCHORS: (0, 0) = SEL color (color of the object to select); (0, w-1) = CODE (transform 1..4: id/rot-cw/rot-180/flip-lr); (h-1, 0) = FRAME color (color of the target hollow rectangular frame). Body contains: (a) ONE hollow rectangular frame in FRAME color (6-7 per side); (b) ONE connected object (2-4 cells) in SEL color (NOT at (0, 0)). Rule: read 3 anchors. Find sel-colored object (excluding (0, 0)) and frame-colored rectangular frame. Transform object by CODE. Fresh 0-canvas with only the frame redrawn. Center-paste transformed object inside the frame interior.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
