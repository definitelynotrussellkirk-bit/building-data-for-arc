# 78fd2bcdbb99

0-bg grid (h×w, ~5-7 by ~7-9) containing a SINGLE-COLOR pattern that is MOSTLY LR-symmetric (more lr-symmetric than ud-symmetric) but has 1-3 'missing' cells where the mirror is non-zero but the cell itself is 0. Rule: count cells where input != lr-mirror (lr-mismatches) and != ud-mirror (ud-mismatches). Pick axis with FEWER mismatches (default lr if tied). For each 0-cell whose mirror is non-zero, copy the mirror color in. Output: completed symmetric pattern.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
