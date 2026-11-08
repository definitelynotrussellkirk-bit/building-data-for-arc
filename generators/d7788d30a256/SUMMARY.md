# d7788d30a256

0-bg grid (h~9-13, w~11-15) with: (a) ONE COLOR-3 (green) BLOB of 3-5 cells at a random clear position (the TEMPLATE); (b) ONE COLOR-7 (orange) ANCHOR cell at a non-adjacent position with enough room for the rotated template; (c) k COLOR-1 (blue) CELLS at scattered positions (1 ≤ k ≤ 4) — k counts the rotation. The template, anchor, and 1-cells are mutually 4-non-adjacent. Rule (ROTATE TEMPLATE BY k, STAMP AT ANCHOR IN COLOR 8): COUNT k = number of color-1 cells. Identify the LARGEST COLOR-3 BLOB (the TEMPLATE). NORMALIZE the template (shift to origin). APPLY transform: k=1 identity, k=2 90° CW, k=3 180°, k=4 horizontal flip. Find the COLOR-7 ANCHOR. STAMP the TRANSFORMED template at the anchor position in COLOR 8. Template, anchor, k-markers stay. Net: blue-count picks rotation, applied to green template, stamped in cyan at orange anchor.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
