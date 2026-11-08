# fb1897956172

Grid (h, w ~8-14) where TOP-LEFT 2×2 holds 4 distinct non-zero KEY COLORS: ka=(0,0), kb=(0,1), kc=(1,0), kd=(1,1). Body (rest of the grid) contains cells in mixed colors including the key colors. Rule: read keys ka, kb, kc, kd. For each cell (r, c) outside the top-left 2×2, if v == ka → swap to kb; if v == kb → swap to ka; if v == kc → swap to kd; if v == kd → swap to kc. Other colors unchanged. The top-left 2×2 is preserved. The body also contains NON-KEY colors, which the rule leaves UNCHANGED (so the swap is shown to be selective, not a global remap). Net effect: two PAIRED color swaps (ka↔kb, kc↔kd) applied only to body cells matching a key color.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
