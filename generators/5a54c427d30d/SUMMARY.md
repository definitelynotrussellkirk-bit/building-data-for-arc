# 5a54c427d30d

0-bg grid (h, w~14-18) with 2-4 MULTI-COLOR 8-CONNECTED COMPONENTS, each a SOLID RECTANGULAR BLOCK (3×3, 4×4, or rect from size_range small/medium/large) in a DISTINCT MAJOR COLOR drawn from a palette excluding {0, 9}. EACH BLOCK has 1-N EMBEDDED COLOR-9 CELLS at random positions within its bbox. The NINE-COUNT per component is DISTINCT (chosen from ascending/wide-spread/tight-spread distributions), so MINIMUM is UNIQUE. Components separated by inter-object margin ≥1. Rule (ERASE THE COMPONENT WITH FEWEST 9-CELLS): find every multi-color 8-CONNECTED COMPONENT (each block + its embedded 9s counts as one). COUNT the 9-cells in each. Identify the component with the UNIQUE MINIMUM 9-count. ERASE (paint all its cells to 0). Other components stay unchanged. Net: the block with the fewest 9-dots gets wiped; all others survive.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
