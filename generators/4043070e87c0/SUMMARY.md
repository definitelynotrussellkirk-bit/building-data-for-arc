# 4043070e87c0

0-bg grid of EVEN HEIGHT (2 × half_h, where half_h ∈ {3..7}) × WIDTH w ∈ {3..14}: (a) TOP HALF (rows 0..half_h-1) filled with TOP_COLOR (non-{0, 2}) via one of 6 PANEL_PATTERNS (random / blob / stripes / checker / border / diagonal) at density 0.3..0.6; (b) BOTTOM HALF (rows half_h..2 * half_h - 1) filled with BOT_COLOR (distinct from {0, 2, top_color}) using the same pattern type at independent density 0.3..0.6. NO SEPARATOR ROW between the halves. At least 1 cell-pair (r, c) has g[r][c] = 0 AND g[half_h+r][c] = 0 (enforced via _ensure_both_zero). Rule (PRODUCE AN h × w OUTPUT: BOTH-ZERO CELL PAIRS BECOME 2, ELSE 0): COMPUTE a fresh half_h × w OUTPUT grid. For EACH (r, c) with r ∈ [0, half_h-1] and c ∈ [0, w-1]: IF g[r][c] = 0 AND g[half_h+r][c] = 0 → output[r][c] = 2; ELSE output[r][c] = 0. The output is HALF the input's height. Net: a cell-wise NOR of the two stacked panels, emitted as 2s on a bg-0 half-height grid.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
