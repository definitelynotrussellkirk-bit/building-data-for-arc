# 1df78fa6eb8c

0-bg grid (h~4-5, w derived) with N=5-6 same-height PANELS each of width 4, separated by FULL COLOR-9 (maroon) DIVIDER COLUMNS of width 1. Each panel holds a CONNECTED MOTIF of 1-3 cells in some non-{0, 9} color (color chosen independently from {2, 3, 4, 5, 6, 7}). Output uniq_out=12 (intrinsic — pair-indication output normalizes across samples). Rule (FIND THE MATCHING PAIR ACROSS PANELS): identify the N PANELS separated by 9-dividers. Detect WHICH TWO PANELS share the same NORMALIZED MOTIF SHAPE (modulo D4 if task-specific). EMIT a MARKER OUTPUT — typically a smaller grid or recolored slice highlighting the pair (e.g., indices, concatenated motifs, or matrix). Net: locate the unique shape-pair among 5-6 panels and emit its identification.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
