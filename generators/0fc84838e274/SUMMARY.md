# 0fc84838e274

0-bg grid (h×w, ~9-11 by ~10-12) with 2-3 COLOR PAIRS: each of 2-3 distinct non-zero colors appears EXACTLY 2 times as single-cell markers (not 4-adjacent), positioned NON-COLINEARLY (different rows AND different cols). For each pair, at least one of the two L-elbow routes between the two endpoints is clear of other pair-cells. Rule: for each color, find its 2 endpoints. Try both L-elbow paths (via (r1, c2) corner or (r2, c1) corner). Pick the one whose interior cells don't pass through any other pair's endpoint cells. Paint that elbow path with the pair's color. Output: each pair connected by its clear elbow.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
