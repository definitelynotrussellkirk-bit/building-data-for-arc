# 3b907ea971ea

0-bg vertical 2-panel layout (top: template panel; bottom: board panel) separated by a COLOR-9 divider. The TEMPLATE is a fixed 3×3 pattern ([[4,5,6],[7,8,2],[3,4,5]]) placed at (1, 1) in the template panel (h-tall × 5-wide). The BOARD (h × w~9-13) contains 2-4 COPIES of the same template stamped at random non-overlapping anchors. Rule: identify the TEMPLATE in the top panel. SCAN the BOARD: for EACH 3×3 window that EXACTLY MATCHES the template (cell-by-cell, all values match), KEEP those template cells. CLEAR (set to 0) every non-matching cell on the board. Output: the board with only matching template instances kept. Net: template panel teaches pattern; output is board cleared except for exact template matches.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
