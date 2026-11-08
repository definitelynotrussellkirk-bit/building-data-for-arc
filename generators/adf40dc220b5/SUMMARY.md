# adf40dc220b5

Grid is split into 3 panels by 2 full color-5 separator columns. Each panel holds exactly one connected non-bg shape. Panels A (left) and B (middle) share the SAME shape and color; the shape's position differs — the translation vector (dr, dc) = bbox_top_left(B) - bbox_top_left(A) is the rule's only learned quantity. Panel C (right) has a (possibly different-colored) shape. Rule output is a C-panel-sized grid containing C's shape translated by (dr, dc); cells that would translate outside C's panel are silently dropped.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
