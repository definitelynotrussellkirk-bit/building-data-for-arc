# 6f2e2e5221f2

0-bg grid with: (a) exactly THREE color-2 (red) cells positioned as three corners of a rectangle (so exactly 2 distinct row values and 2 distinct col values); (b) 0-3 DECORATION cells in OTHER non-{0, 2, 8} colors that the rule preserves but ignores. Rule: find all color-2 cells. Compute rs = unique rows, cs = unique cols. corners = product rs × cs (4 candidate corner cells). The rectangle has both dimensions at least 3 cells, and may include 0-4 non-{0,2,8} decoration cells away from the red corners. missing = first corner not already in pts. Set missing to 8. Output = input with the missing corner painted 8.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
