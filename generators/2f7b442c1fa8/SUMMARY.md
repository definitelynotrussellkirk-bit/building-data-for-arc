# 2f7b442c1fa8

0-bg grid with N (3-5) isolated 4-connected components, each in a distinct color (sampled freely from {1..9}). The components are scattered so no two 4-touch each other and no two share an 8-edge. Rule: collect all components, sort by their bbox top-left in reading order (row then column). Recolor in order with the palette [2, 3, 4, 5, 6, 7, 8, 9, 1]: first → 2, second → 3, third → 4, etc. Output places the recolored cells on a fresh 0-bg grid (positions preserved, only colors changed).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
