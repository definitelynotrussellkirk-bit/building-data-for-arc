# 388e9ae29018

Fixed 15×15 color-7 (orange) bg grid with: (a) a RED DIAMOND OUTLINE — color 2 cells at all positions where Manhattan distance from a center (red_r, red_c) equals red_radius (2 or 3); (b) a GRAY DIAMOND OUTLINE — color 5 cells at all positions where Manhattan distance from a center (gray_r, gray_c) equals gray_radius (1 or 2). Diamonds are positioned with margin so growth/shrink stays in-bounds. Rule: detect each diamond. RED diamond SHRINKS by 1 (replace red cells with bg, redraw at red_radius - 1). GRAY diamond GROWS by 1 (redraw at gray_radius + 1). Output: bg + shrunk red diamond + grown gray diamond.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
