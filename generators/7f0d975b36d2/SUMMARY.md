# 7f0d975b36d2

13×13 grid filled mostly with color 5 (gray) background. At center (6, 6) is a PARTIAL PLUS marked with 4 color-2 (red) cells at the cardinal arm positions: (6,5)(6,7)(5,6)(7,6). A few sparse cells outside the center are noise (random 0 or 5). Rule: scan all color-2 cells. Cluster them per row by proximity (≤4 cols apart). For each cluster of ≥2 two-cells, infer the plus's center column = avg of the cluster's col span, radius = max distance to avg. Then check column candidates for column matches. For each inferred plus center (cr, cc): paint every color-5 cell on the plus's horizontal arm (cr, cc-r..cc+r) AND vertical arm (cr-r..cr+r, cc) to color 8 (cyan). Color-2 cells stay. Net effect: complete the plus by filling its arms in cyan.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
