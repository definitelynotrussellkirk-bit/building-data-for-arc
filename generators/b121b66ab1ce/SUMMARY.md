# b121b66ab1ce

0-bg grid (h ∈ 9-13, w ∈ 10-14) with: (a) ONE COLOR-1 (BLUE) TEMPLATE SHAPE drawn from base_shapes bank (4 variants of 3-4 cell shapes: S, Z, T, L) placed at a random non-overlapping interior position via _free check; (b) ONE MATCHING COLOR-3 (GREEN) SHAPE — same variant as the template — placed at another random position; (c) WITH 70% PROBABILITY ONE ADDITIONAL DIFFERENT COLOR-3 SHAPE — a different variant from base_shapes (acts as a distractor). Rule (FIND THE UNIQUE COLOR-1 TEMPLATE; AMONG COLOR-3 SHAPES, KEEP ONLY THOSE WHOSE NORMALIZED BINARY MASK EXACTLY MATCHES THE TEMPLATE; RECOLOR KEPT ONES TO COLOR 8): EXTRACT the COLOR-1 component → normalize its cells (subtract min r/c). EXTRACT every color-3 component. For EACH: normalize its cells; CHECK if EQUAL to template's normalized cells. IF YES: RECOLOR every cell of that component to COLOR 8 (cyan). ELSE: ERASE it to 0. The color-1 template stays. Net: the matching green copy becomes cyan; non-matching green distractors vanish.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
