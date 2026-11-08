# 70c1f7fc5056

0-bg grid (h~8-11, w~9-12) with: (a) ONE small PROTOTYPE BLOB of 2-4 cells in some non-{0, 9} color, placed at a random position (this is the SHAPE to be stamped); (b) 1-2 color-9 (maroon) ANCHOR single cells placed at positions that have room for the full prototype stamp to fit in-bounds without overlapping existing cells. Rule: extract the prototype's shape cells (the non-9, non-0 connected blob). Build an EMPTY OUTPUT GRID of the same dims. For each color-9 ANCHOR, STAMP the prototype's shape ANCHORED at the anchor's position (with anchor as the stamp's top-left), painted in the prototype's original color. Original prototype + anchors are DISCARDED from output. Net: anchors become stamp positions; output is the prototype replicated at each anchor.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
