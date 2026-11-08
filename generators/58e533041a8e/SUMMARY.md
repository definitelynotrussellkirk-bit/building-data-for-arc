# 58e533041a8e

0-bg grid (h, w ∈ 4-18, by difficulty) with: each ROW INDEPENDENTLY assigned a KIND per ROW_DISTRIBUTION ∈ {uniform, biased_match, biased_mismatch, alternating}: (a) 'match' → g[r][0] = g[r][w-1] = SAME color drawn from palette; (b) 'mismatch' → g[r][0] = a, g[r][w-1] = b (different colors); (c) 'blank' → both left and right are 0. Palette of 2-6 distinct colors drawn from {1..9}. INTERIOR DECOY DENSITY ∈ 0-20% sprinkles random colored cells in non-edge columns. Generation guarantees ≥1 matching-row exists. Rule (FOR EACH ROW r: IF g[r][0] != 0 AND g[r][0] == g[r][w-1]: FILL THE ENTIRE ROW (ALL w COLUMNS) WITH THAT COLOR; ELSE: KEEP THE ROW AS-IS): For EACH row r: READ g[r][0] and g[r][w-1]. IF both are non-zero AND equal: PAINT every cell of that row with that color. OTHERWISE: row unchanged. Net: matching-pair rows fill solidly with their edge color; mismatch and blank rows stay.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
