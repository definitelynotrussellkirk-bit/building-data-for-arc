# 04de9df58814

0-bg grid (h, w~12-18) with ≥2 GREEN(3) RECTANGULAR COMPONENTS: (a) ≥1 BORDER-TOUCHING GREEN — a solid 3-color rectangle (h~2-4, w~2-4) anchored to one of the 4 grid edges (top/bottom/left/right); (b) ≥1 INTERIOR GREEN — a solid 3-color rectangle placed in the interior (margin ≥1 from every edge) at a non-overlapping position. Rule (RECOLOR BORDER-TOUCHING GREENS, KEEP INTERIOR GREENS): Find all 4-CONNECTED COMPONENTS of color 3. For EACH component: if ANY cell is on the OUTER BORDER (row 0, row h-1, col 0, col w-1), RECOLOR every cell of that component to a different color (puzzle-specific). Else (fully interior), keep at 3. Net: border-anchored greens get a new color; interior greens stay green.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
