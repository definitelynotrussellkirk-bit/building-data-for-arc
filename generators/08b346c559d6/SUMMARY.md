# 08b346c559d6

0-bg grid (h EVEN ~6-8, w~6-9). UPPER HALF (rows 0..h/2-1) contains 3-6 SOURCE MARKER cells scattered at random positions in various non-bg colors. LOWER HALF (rows h/2..h-1) often contains DISTRACTOR rows — each row painted in a single solid color from 1..9 with ~75% probability — that will be OVERWRITTEN by the rule. Rule: COPY the UPPER HALF into the LOWER HALF using a VERTICAL MIRROR — for each cell (r, c) in the upper half (r < h/2), PAINT (h-1-r, c) with the value of (r, c). The distractors in the lower half are OVERWRITTEN. Net: input has an upper-half pattern + random lower-half noise; output is the grid with vertical mirror symmetry about the horizontal midline.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
