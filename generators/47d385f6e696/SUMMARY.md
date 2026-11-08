# 47d385f6e696

0-bg grid (h~9-11, w~11-13) with: (a) OUTER RECT FRAME at (1, 1)..(h-2, w-2) in COLOR A (from palette); (b) INNER RECT FRAME at (3, 3)..(h-4, w-4) inside, in COLOR B (different); (c) ≥1 COLOR-1 DOT inside the INNER frame's interior, ≥1 BETWEEN the inner and outer frames. Rule (RECOLOR 1-DOTS BY DEEPEST ENCLOSING FRAME): for EACH COLOR-1 DOT at (r, c), find the SMALLEST (deepest-nested) RECT-FRAME that STRICTLY ENCLOSES the dot. RECOLOR the dot to that frame's COLOR. If no frame encloses (dot outside outer), the dot STAYS color 1. Net: 1-dots get repainted by the deepest enclosing frame's color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
