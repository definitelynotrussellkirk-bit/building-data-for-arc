# 287967e33b21

0-bg grid (h~8-11, w~8-11) with multiple DISCONNECTED color-7 (orange) OBJECTS — some TOUCHING the grid OUTER BORDER (row 0, last row, first col, or last col) and at least ONE objects STRICTLY INTERIOR (not touching any border). Input is strictly 2-colour {0, 7} (no decoys). Rule: identify each connected color-7 component. ERASE (set to 0) every color-7 component that has AT LEAST ONE cell on the outer border. KEEP color-7 components whose cells are all strictly interior. Net: orange blobs touching the edge of the canvas vanish; interior orange blobs survive.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
