# d476983a3d6c

Fixed 10×10 grid with: (a) cell (0, 0) holds a COMMAND CODE in {1, 2} (the L-path order selector); (b) 2-4 SAME-COLOR MARKER PAIRS in colors chosen to AVOID the command color, each pair being 2 single cells at distinct rows AND distinct columns (non-aligned). Pairs don't share positions; total markers ≤ 2*n_pairs. Rule (KEY-DIRECTED L-PATH DRAW): READ the command (0, 0). For EACH SAME-COLOR PAIR at p1=(r1, c1), p2=(r2, c2), DRAW an L-SHAPED PATH connecting them: cmd=1 → HORIZONTAL FIRST then VERTICAL (bend at (r1, c2)); cmd=2 → VERTICAL FIRST then HORIZONTAL (bend at (r2, c1)). PAINT the L in the pair's COLOR. The command cell stays. Net: each marker pair gets an L-path between them; cmd picks bend orientation.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
