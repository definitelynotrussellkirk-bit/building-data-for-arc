# 0f6ba01fa18c

8×10 0-bg grid with: (a) one connected color-1 (blue) TEMPLATE A; (b) one connected color-2 (red) TEMPLATE B; (c) exactly one SINGLETON KEY cell with color ∈ {3, 4, 6} placed somewhere apart. Rule: extract A's cells and normalize → s1; same for B's cells → s2. Detect control color (the one with count == 1 in {3, 4, 6}). Apply boolean op on the two normalized cell-sets: 3 → UNION, 4 → INTERSECTION, 6 → XOR (symmetric difference). If result empty → output [[0]]. Else: normalize result to (0, 0), paint cells color 8 (cyan). Output: small grid sized to result's bbox.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
