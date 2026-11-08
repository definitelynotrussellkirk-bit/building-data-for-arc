# 027805c8ff0f

0-bg N x (3N+2) grid: three square N x N panels A | B | C split by two full-height blue(1) divider columns. B = t(A) for t in {1=id 2=cw 3=180 4=transpose 5=flip-lr 6=flip-ud}; C holds an independent shape. Rule: crop each panel to content, find the FIRST t (in 1..6 order) with t(crop A) == crop B, and output t(crop C) — a small cropped grid, NOT the 3-panel layout.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
