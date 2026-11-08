# de45fc71c193

0-bg grid (h~6-9, w~8-11) with HARDCODED POSITIONS for 2 DISTINCT colors: (a) COLOR_A (random from {2..7}) at fixed positions (1, 1) and (h-3, w//2+1) — defining bbox A; (b) COLOR_B (distinct) at fixed positions (2, w//2-1) and (h-2, w-2) — defining bbox B. Hardcoded positions × color pair choices ≈ ~50 unique. Output uniq_out=15 (intrinsic — intersection rect dimensions × colors normalize). Rule (PAINT INTERSECTION OF BBOXES IN 8): For EACH NON-0 COLOR: COMPUTE BBOX from its cells. COMPUTE bbox_A ∩ bbox_B — the RECTANGULAR INTERSECTION. PAINT every cell inside that intersection rect with COLOR-8 (cyan). Original color cells stay. Net: bbox overlap rect becomes cyan.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
