# 726ac4a5071a

0-bg grid (h~3-5, w~10-14) where EACH ROW r contains a PERIODIC PREFIX: a cycle of length P_r ∈ {1, 2, 3} repeated K_r ≥ 2 times starting at col 0, followed by TRAILING 0-CELLS to col w-1. The prefix length K_r * P_r < w (so trailing 0s exist). Each row's period uses a random selection of colors from {1..9}. Rule (INFER ROW PERIOD, EXTEND PREFIX TO FILL ENTIRE ROW): For EACH ROW r: DETECT the PERIODIC CYCLE by finding the smallest period length P that makes the prefix self-repeating. EXTEND the cycle by repeating the period FROM CELL 0 all the way TO COL w-1. Trailing 0s get filled with cycle continuation. Net: each row's periodic prefix extends to fill the full row width.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
