# d8c1699fa902

0-bg grid (h~9-11, w~12-14) with: (a) RANK-KEY at (0, 0) — a color encoding rank ∈ {1, 2, 3} (1-indexed size rank ascending); (b) TF-KEY at (0, w-1) — a color encoding transform ∈ {4, 5, 6, 7}: 4=IDENTITY, 5=ROTATE CW, 6=FLIP LR, else=ROTATE 180; (c) BODY (rows ≥1) — 3 CONNECTED COMPONENTS in DISTINCT SIZES (2..6) drawn from a shape bank in 3 distinct BODY COLORS (excluding rank-key and tf-key colors). Components are non-touching with 1-cell padding. Rule (SORT BODY COMPONENTS BY SIZE ASC, PICK RANK-KEY-TH, APPLY TF-KEY TRANSFORM): identify the 2 corner key cells. SORT all body components by CELL COUNT ASC. PICK the rank-key-th (1-indexed). CROP that component to its BBOX. APPLY the TF-KEY transform (identity / cw90 / flip-lr / rot180) to the crop. OUTPUT is the transformed crop. Net: rank-key selects which size-ranked blob to pull, tf-key selects how to rotate/flip it.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
