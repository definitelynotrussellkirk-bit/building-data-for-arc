# 1fe5538001fe

0-bg grid with ODD h,w (~7-13) split into 4 quadrants by a central all-0 separator row (h//2) and column (w//2). A random connected blob (2-5 cells) in one non-bg colour is placed in one quadrant and its flip-lr / flip-ud / 180 mirrors in the others, then EXACTLY ONE quadrant is erased (all-zero = 'missing'). Rule: find the missing (all-zero) quadrant and a filled source quadrant; mirror the source into the missing slot (flip-ud across the row split, flip-lr across the col split). Output: the completed mirror-symmetric grid.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
