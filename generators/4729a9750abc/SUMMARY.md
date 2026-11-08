# 4729a9750abc

Grid with 2-3 hollow color-9 rectangular FRAMES side by side. Each frame has: (a) a SEL-KEY cell above (in row r1-1) with value 2 (pick smallest) or 3 (pick largest); (b) a TR-KEY cell to the left (in col c1-1) with value 3 (identity), 4 (rot-CW), 5 (flip-lr), or 6 (rot-180); (c) inside, ≥2 components in distinct non-{0,9} colors with STRICTLY DISTINCT sizes. Rule: for each frame, pick the chosen interior component (smallest if sel=2, largest if sel=3). Crop to bbox. Apply the TR-key transform. Hstack all transformed parts with 1-col gap, vertically centered.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
