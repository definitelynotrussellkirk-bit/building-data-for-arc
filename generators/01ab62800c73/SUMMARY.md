# 01ab62800c73

Grid with: (a) row 0 = sequence of transform codes (cells in {1, 2, 3, 4}, padded with 0s); (b) rows 1+ = one asymmetric shape — single- or multi-color, and the colors MAY come from {1..4} (codes live only in row 0). Rule: extract non-zero values from row 0 (in order). Body = rows 1+ cropped to non-zero. Apply ops sequentially: 1=flip-lr, 2=flip-ud, 3=rot-cw, 4=rot-180. Output is the transformed crop.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
