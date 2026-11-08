# 3146e0c9c3af

0-bg grid (size varies). 2-5 NESTED color-1 (blue) RECTANGULAR FRAMES, each inset >=2 on every side from the one outside it (so they are separate components; insets vary per side, not necessarily concentric). Rule: for each empty cell, count how many frame interiors enclose it (depth); if depth > 0, recolor it to depth+1 (depth-1 -> color 2, depth-2 -> color 3, ...). The frames stay color 1 and outside cells stay 0. The grid size, the number of frames and their per-side insets all vary freely, so the depth gradient (the output) varies too (was centered concentric frames + grid padding).

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
